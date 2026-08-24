"""Azure configuration and service initialization."""

import os
from typing import Optional
from azure.identity import DefaultAzureCredential, ClientSecretCredential, EnvironmentCredential
from azure.storage.blob import BlobServiceClient
from azure.keyvault.secrets import SecretClient
from azure.data.tables import TableServiceClient
from azure.cosmos import CosmosClient
from azure.monitor.opentelemetry import configure_azure_monitor


class AzureConfig:
    """Azure configuration and credentials management."""

    def __init__(self):
        self.subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        self.resource_group = os.getenv('AZURE_RESOURCE_GROUP')
        
        # Service endpoints
        self.keyvault_url = os.getenv('AZURE_KEYVAULT_URL')
        self.storage_account_url = os.getenv('AZURE_STORAGE_ACCOUNT_URL')
        self.cosmos_endpoint = os.getenv('AZURE_COSMOS_ENDPOINT')
        self.sql_server = os.getenv('AZURE_SQL_SERVER')
        self.sql_database = os.getenv('AZURE_SQL_DATABASE')
        
        # Monitoring
        self.app_insights_connection_string = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
        
        # Initialize credentials
        self.credential = self._get_credential()

    def _get_credential(self):
        """Get Azure credential based on environment."""
        # Try service principal first (for CI/CD)
        if self.client_id and self.client_secret and self.tenant_id:
            return ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
        # Fall back to default credential (Managed Identity, CLI, VS Code, etc.)
        return DefaultAzureCredential()


class AzureServices:
    """Azure service clients factory."""

    def __init__(self, config: AzureConfig):
        self.config = config
        self._blob_client: Optional[BlobServiceClient] = None
        self._keyvault_client: Optional[SecretClient] = None
        self._table_client: Optional[TableServiceClient] = None
        self._cosmos_client: Optional[CosmosClient] = None

    @property
    def blob_service_client(self) -> BlobServiceClient:
        """Get or create Blob Storage client."""
        if self._blob_client is None:
            self._blob_client = BlobServiceClient(
                account_url=self.config.storage_account_url,
                credential=self.config.credential
            )
        return self._blob_client

    @property
    def keyvault_client(self) -> SecretClient:
        """Get or create Key Vault client."""
        if self._keyvault_client is None:
            self._keyvault_client = SecretClient(
                vault_url=self.config.keyvault_url,
                credential=self.config.credential
            )
        return self._keyvault_client

    @property
    def table_service_client(self) -> TableServiceClient:
        """Get or create Table Storage client."""
        if self._table_client is None:
            self._table_client = TableServiceClient(
                account_url=self.config.storage_account_url,
                credential=self.config.credential
            )
        return self._table_client

    @property
    def cosmos_client(self) -> CosmosClient:
        """Get or create Cosmos DB client."""
        if self._cosmos_client is None:
            self._cosmos_client = CosmosClient(
                url=self.config.cosmos_endpoint,
                credential=self.config.credential
            )
        return self._cosmos_client

    def configure_monitoring(self) -> None:
        """Configure Azure Monitor and Application Insights."""
        if self.config.app_insights_connection_string:
            configure_azure_monitor(
                connection_string=self.config.app_insights_connection_string
            )
