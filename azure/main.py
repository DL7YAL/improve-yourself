"""Main application with Azure integration."""

import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.azure_config import AzureConfig, AzureServices
from services.azure_storage import AzureStorageService
from services.azure_keyvault import AzureKeyVaultService
from services.azure_database import AzureCosmosService, AzureSQLService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ApplicationContext:
    """Application context with all Azure services."""

    def __init__(self):
        self.config = AzureConfig()
        self.services = AzureServices(self.config)

        # Initialize service clients
        self.storage = AzureStorageService(self.services)
        self.keyvault = AzureKeyVaultService(self.services)

        # Setup monitoring
        self.services.configure_monitoring()

        logger.info("Application context initialized with Azure services")

    def initialize_databases(self):
        """Initialize database connections."""
        # SQL Database
        if self.config.sql_server and self.config.sql_database:
            try:
                sql_password = self.keyvault.get_secret('sql-password')
                self.sql = AzureSQLService(
                    server=self.config.sql_server,
                    database=self.config.sql_database,
                    username='sqladmin',
                    password=sql_password
                )
                logger.info("SQL Database connection established")
            except Exception as e:
                logger.error(f"Failed to initialize SQL Database: {e}")

        # Cosmos DB
        if self.config.cosmos_endpoint:
            try:
                self.cosmos = AzureCosmosService(
                    cosmos_client=self.services.cosmos_client,
                    database_name='improve-yourself',
                    container_name='data'
                )
                logger.info("Cosmos DB connection established")
            except Exception as e:
                logger.error(f"Failed to initialize Cosmos DB: {e}")


def main():
    """Main application entry point."""
    try:
        app_context = ApplicationContext()
        app_context.initialize_databases()

        logger.info("Application started successfully with full Azure integration")

        # Example usage
        # Upload a file
        # with open('example.txt', 'rb') as f:
        #     url = app_context.storage.upload_blob('uploads', 'example.txt', f)
        #     logger.info(f"File uploaded to: {url}")

        # Get a secret
        # secret = app_context.keyvault.get_secret('my-secret')
        # logger.info(f"Retrieved secret: {secret[:10]}...")

    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
