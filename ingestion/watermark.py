from datetime import datetime, timezone

import snowflake.connector

from ingestion.config import Config
from ingestion.logger import get_logger

logger = get_logger(__name__)

SOURCE_NAME = "aviationstack_flights"


class WatermarkManager:

    def __init__(self):
        try:
            self.conn = snowflake.connector.connect(
                account=Config.SNOWFLAKE_ACCOUNT,
                user=Config.SNOWFLAKE_USER,
                password=Config.SNOWFLAKE_PASSWORD,
                warehouse=Config.SNOWFLAKE_WAREHOUSE,
                database=Config.SNOWFLAKE_DATABASE,
                schema="CONTROL",
            )
            logger.info("Connected to Snowflake for watermark tracking.")
        except Exception:
            logger.exception("Failed to connect to Snowflake for watermark tracking.")
            raise

    def _current_month_str(self):
        return datetime.now(timezone.utc).strftime("%Y-%m")

    def check_quota(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "SELECT requests_used_this_month, usage_month "
                "FROM CONTROL.WATERMARKS WHERE source_name = %s",
                (SOURCE_NAME,),
            )
            row = cursor.fetchone()

            if row is None:
                logger.error(
                    "No watermark row found for source_name=%s. "
                    "Did you seed CONTROL.WATERMARKS?",
                    SOURCE_NAME,
                )
                return False

            requests_used, usage_month = row
            current_month = self._current_month_str()

            if usage_month != current_month:
                logger.info(
                    "Month rollover detected (%s -> %s). Resetting quota counter.",
                    usage_month,
                    current_month,
                )
                cursor.execute(
                    "UPDATE CONTROL.WATERMARKS "
                    "SET requests_used_this_month = 0, usage_month = %s, "
                    "updated_at = CURRENT_TIMESTAMP() "
                    "WHERE source_name = %s",
                    (current_month, SOURCE_NAME),
                )
                self.conn.commit()
                requests_used = 0

            if requests_used >= Config.MAX_REQUESTS_PER_MONTH:
                logger.warning(
                    "Quota exhausted: %s/%s requests used this month (%s). "
                    "Skipping extraction.",
                    requests_used,
                    Config.MAX_REQUESTS_PER_MONTH,
                    current_month,
                )
                return False

            logger.info(
                "Quota check passed: %s/%s requests used this month (%s).",
                requests_used,
                Config.MAX_REQUESTS_PER_MONTH,
                current_month,
            )
            return True

        finally:
            cursor.close()

    def increment_usage(self, batch_id, requests_made=1):
        """Call after a successful extraction to record usage."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "UPDATE CONTROL.WATERMARKS "
                "SET requests_used_this_month = requests_used_this_month + %s, "
                "last_successful_run = CURRENT_TIMESTAMP(), "
                "last_batch_id = %s, "
                "updated_at = CURRENT_TIMESTAMP() "
                "WHERE source_name = %s",
                (requests_made, batch_id, SOURCE_NAME),
            )
            self.conn.commit()
            logger.info(
                "Watermark updated. batch_id=%s, requests_made=%s",
                batch_id,
                requests_made,
            )
        finally:
            cursor.close()

    def close(self):
        try:
            self.conn.close()
            logger.info("Watermark manager connection closed.")
        except Exception:
            logger.exception("Error while closing watermark manager connection.")