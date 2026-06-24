import json
import uuid

import snowflake.connector

from ingestion.config import Config
from ingestion.logger import get_logger

logger = get_logger(__name__)


class SnowflakeLoader:
    """Handles idempotent loads of raw flight payloads into RAW.FLIGHTS_RAW."""

    def __init__(self):
        try:
            self.conn = snowflake.connector.connect(
                account=Config.SNOWFLAKE_ACCOUNT,
                user=Config.SNOWFLAKE_USER,
                password=Config.SNOWFLAKE_PASSWORD,
                warehouse=Config.SNOWFLAKE_WAREHOUSE,
                database=Config.SNOWFLAKE_DATABASE,
                schema="RAW",
            )
            logger.info("Connected to Snowflake for raw data loading.")
        except Exception:
            logger.exception("Failed to connect to Snowflake.")
            raise

    def load_batch(
        self,
        flight_records,
        batch_id,
        pipeline_run_id,
        source_endpoint,
    ):
        """
        Idempotently loads a list of raw flight JSON records into RAW.FLIGHTS_RAW.

        Strategy:
        - Delete any existing rows for the batch_id.
        - Insert the latest records.
        """

        cursor = None

        try:
            cursor = self.conn.cursor()

            # Delete existing records for this batch (idempotent load)
            cursor.execute(
                "DELETE FROM RAW.FLIGHTS_RAW WHERE batch_id = %s",
                (batch_id,),
            )

            deleted_count = cursor.rowcount

            if deleted_count > 0:
                logger.info(
                    "Deleted %s existing rows for batch_id=%s.",
                    deleted_count,
                    batch_id,
                )
            else:
                logger.info(
                    "No existing rows found for batch_id=%s.",
                    batch_id,
                )

            logger.info(
                "Loading %s flight records into RAW.FLIGHTS_RAW.",
                len(flight_records),
            )

            insert_sql = """
                INSERT INTO RAW.FLIGHTS_RAW (
                    raw_id,
                    source_endpoint,
                    batch_id,
                    pipeline_run_id,
                    ingestion_timestamp,
                    raw_payload
                )
                SELECT
                    %s,
                    %s,
                    %s,
                    %s,
                    CURRENT_TIMESTAMP(),
                    PARSE_JSON(%s)
            """

            rows_inserted = 0

            for record in flight_records:
                cursor.execute(
                    insert_sql,
                    (
                        str(uuid.uuid4()),
                        source_endpoint,
                        batch_id,
                        pipeline_run_id,
                        json.dumps(record),
                    ),
                )
                rows_inserted += 1

            self.conn.commit()

            logger.info(
                "Successfully loaded %s rows into RAW.FLIGHTS_RAW for batch_id=%s.",
                rows_inserted,
                batch_id,
            )

            return rows_inserted

        except Exception:
            self.conn.rollback()

            logger.exception(
                "Failed to load batch into RAW.FLIGHTS_RAW. batch_id=%s",
                batch_id,
            )

            raise

        finally:
            if cursor is not None:
                cursor.close()

    def close(self):
        try:
            self.conn.close()
            logger.info("Snowflake loader connection closed.")
        except Exception:
            logger.exception("Error while closing Snowflake loader connection.")