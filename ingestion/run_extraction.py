import uuid
from datetime import datetime, timezone

from ingestion.audit import AuditLogger
from ingestion.aviationstack_client import AviationStackClient
from ingestion.logger import get_logger
from ingestion.snowflake_loader import SnowflakeLoader
from ingestion.watermark import WatermarkManager

logger = get_logger(__name__)


def generate_batch_id():
    """Generate a batch ID based on the current UTC hour."""
    now = datetime.now(timezone.utc)
    return now.strftime("batch_%Y%m%d_%H")


def run():
    pipeline_run_id = str(uuid.uuid4())
    batch_id = generate_batch_id()
    execution_start = datetime.now(timezone.utc)

    logger.info(
        "Starting pipeline. run_id=%s, batch_id=%s",
        pipeline_run_id,
        batch_id,
    )

    client = AviationStackClient()
    loader = SnowflakeLoader()
    audit = AuditLogger()
    watermark = WatermarkManager()

    rows_extracted = 0
    rows_loaded = 0
    execution_status = "FAILED"
    failure_reason = None

    try:
        # Check monthly API quota before making a request.
        if not watermark.check_quota():
            logger.warning("Monthly API quota exhausted. Skipping extraction.")
            execution_status = "SKIPPED"
            failure_reason = "Monthly API quota exhausted"
            return

        response = client.fetch_flights(limit=100, offset=0)

        flight_records = response["data"]
        rows_extracted = len(flight_records)

        logger.info(
            "API returned pagination.count=%s, actual records=%s",
            response["pagination"]["count"],
            rows_extracted,
        )

        rows_loaded = loader.load_batch(
            flight_records=flight_records,
            batch_id=batch_id,
            pipeline_run_id=pipeline_run_id,
            source_endpoint="/v1/flights",
        )

        # Update monthly API usage after a successful load.
        watermark.increment_usage(batch_id)

        execution_status = "SUCCESS"

        logger.info(
            "Pipeline completed successfully. Rows extracted=%s, rows loaded=%s",
            rows_extracted,
            rows_loaded,
        )

    except Exception as e:
        failure_reason = str(e)

        logger.exception(
            "Pipeline execution failed. run_id=%s",
            pipeline_run_id,
        )
        raise

    finally:
        execution_end = datetime.now(timezone.utc)

        try:
            audit.log_run(
                pipeline_run_id=pipeline_run_id,
                execution_start=execution_start,
                execution_end=execution_end,
                rows_extracted=rows_extracted,
                rows_loaded=rows_loaded,
                rows_rejected=max(0, rows_extracted - rows_loaded),
                execution_status=execution_status,
                failure_reason=failure_reason,
            )
        except Exception:
            logger.exception(
                "Failed to write audit log. run_id=%s",
                pipeline_run_id,
            )

        try:
            loader.close()
        except Exception:
            logger.exception("Failed to close Snowflake loader.")

        try:
            audit.close()
        except Exception:
            logger.exception("Failed to close audit logger.")

        try:
            watermark.close()
        except Exception:
            logger.exception("Failed to close watermark manager.")

        logger.info(
            "Pipeline resources closed. run_id=%s",
            pipeline_run_id,
        )


if __name__ == "__main__":
    run()