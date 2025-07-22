"""
Application Configuration

This is the main configuration file that defines the application behavior.
The main table name specified here is the source of truth for all data operations.
"""


class AppConfig:
    """
    Application configuration class.

    To adapt this application to a different database schema:
    1. Change MAIN_TABLE to your primary data table name
    2. Update the database schema accordingly
    3. Everything else will be auto-discovered
    """

    # The main entity table name (source of truth for all data)
    # This table should contain foreign keys to all navigation entities
    MAIN_TABLE: str = "datasets"

    # Application branding
    APP_TITLE: str = "FCC Physics Datasets"
    APP_DESCRIPTION: str = "Search and explore FCC physics simulation datasets and data"

    # API configuration
    API_TIMEOUT: int = 30
    MAX_PAGE_SIZE: int = 100
    DEFAULT_PAGE_SIZE: int = 20

    # Database configuration
    DATABASE_POOL_MIN_SIZE: int = 5
    DATABASE_POOL_MAX_SIZE: int = 20


# Global configuration instance
app_config = AppConfig()
