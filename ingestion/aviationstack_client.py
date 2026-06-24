import time

import requests

from ingestion.config import Config
from ingestion.logger import get_logger

logger = get_logger(__name__)


class AviationStackClient:
    """Client for retrieving flight data from the AviationStack API."""

    def __init__(self):
        self.api_key = Config.AVIATIONSTACK_API_KEY
        self.base_url = Config.AVIATIONSTACK_BASE_URL
        self.max_retries = Config.MAX_RETRIES
        self.timeout = Config.REQUEST_TIMEOUT_SECONDS

    def fetch_flights(self, limit=100, offset=0):
        params = {
            "access_key": self.api_key,
            "limit": limit,
            "offset": offset,
        }

        attempt = 0

        while attempt < self.max_retries:
            attempt += 1

            try:
                logger.info(
                    "Fetching flights (attempt %s/%s, limit=%s, offset=%s)",
                    attempt,
                    self.max_retries,
                    limit,
                    offset,
                )

                response = requests.get(
                    self.base_url,
                    params=params,
                    timeout=self.timeout,
                )

            except requests.exceptions.Timeout:
                wait = 2 ** attempt
                logger.warning(
                    "Request timed out (attempt %s/%s). Retrying in %s seconds.",
                    attempt,
                    self.max_retries,
                    wait,
                )
                time.sleep(wait)
                continue

            except requests.exceptions.ConnectionError:
                wait = 2 ** attempt
                logger.warning(
                    "Connection error (attempt %s/%s). Retrying in %s seconds.",
                    attempt,
                    self.max_retries,
                    wait,
                )
                time.sleep(wait)
                continue

            except requests.exceptions.RequestException:
                logger.exception(
                    "Unexpected request error while calling AviationStack API."
                )
                raise

            if response.status_code == 200:
                logger.info("Successfully fetched flight data.")
                return response.json()

            if response.status_code in (401, 403):
                logger.error(
                    "Authentication failed (HTTP %s): %s",
                    response.status_code,
                    response.text,
                )
                raise RuntimeError(
                    f"Authentication failed (HTTP {response.status_code}). "
                    "Check AVIATIONSTACK_API_KEY."
                )

            if response.status_code == 429:
                wait = (2 ** attempt) * 5
                logger.warning(
                    "Rate limited (HTTP 429). Retrying in %s seconds.",
                    wait,
                )
                time.sleep(wait)
                continue

            if 500 <= response.status_code < 600:
                wait = 2 ** attempt
                logger.warning(
                    "Server error (HTTP %s). Retrying in %s seconds.",
                    response.status_code,
                    wait,
                )
                time.sleep(wait)
                continue

            logger.error(
                "Unexpected HTTP %s: %s",
                response.status_code,
                response.text,
            )

            raise RuntimeError(
                f"Unexpected HTTP {response.status_code}: {response.text}"
            )

        logger.error(
            "Exhausted %s retries calling AviationStack API.",
            self.max_retries,
        )

        raise RuntimeError(
            f"Exhausted {self.max_retries} retries calling AviationStack API."
        )