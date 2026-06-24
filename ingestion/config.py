import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    AVIATIONSTACK_API_KEY = os.environ["AVIATIONSTACK_API_KEY"]
    AVIATIONSTACK_BASE_URL = "http://api.aviationstack.com/v1/flights"

    SNOWFLAKE_ACCOUNT = os.environ["SNOWFLAKE_ACCOUNT"]
    SNOWFLAKE_USER = os.environ["SNOWFLAKE_USER"]
    SNOWFLAKE_PASSWORD = os.environ["SNOWFLAKE_PASSWORD"]
    SNOWFLAKE_WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
    SNOWFLAKE_DATABASE = os.environ.get("SNOWFLAKE_DATABASE", "FLIGHT_TRACKING")

    MAX_REQUESTS_PER_MONTH = int(os.environ.get("MAX_REQUESTS_PER_MONTH", 100))
    MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))
    REQUEST_TIMEOUT_SECONDS = int(os.environ.get("REQUEST_TIMEOUT_SECONDS", 15))