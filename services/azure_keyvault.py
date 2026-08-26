"""Azure Key Vault service for secrets management."""

import logging
from typing import Optional
from azure.keyvault.secrets import SecretProperties
from config.azure_config import AzureServices

logger = logging.getLogger(__name__)


class AzureKeyVaultService:
    """Handle Azure Key Vault operations."""

    def __init__(self, azure_services: AzureServices):
        self.keyvault_client = azure_services.keyvault_client

    def set_secret(self, name: str, value: str, tags: Optional[dict] = None) -> None:
        """Set a secret in Key Vault.

        Args:
            name: Secret name
            value: Secret value
            tags: Optional tags for the secret
        """
        try:
            properties = self.keyvault_client.set_secret(name, value, tags=tags)
            logger.info(f"Secret set: {name}")
        except Exception as e:
            logger.error(f"Error setting secret {name}: {e}")
            raise

    def get_secret(self, name: str) -> str:
        """Retrieve a secret from Key Vault.

        Args:
            name: Secret name

        Returns:
            Secret value
        """
        try:
            secret = self.keyvault_client.get_secret(name)
            return secret.value
        except Exception as e:
            logger.error(f"Error getting secret {name}: {e}")
            raise

    def delete_secret(self, name: str) -> None:
        """Delete a secret from Key Vault.

        Args:
            name: Secret name
        """
        try:
            self.keyvault_client.delete_secret(name)
            logger.info(f"Secret deleted: {name}")
        except Exception as e:
            logger.error(f"Error deleting secret {name}: {e}")
            raise

    def list_secrets(self) -> list:
        """List all secrets in Key Vault.

        Returns:
            List of secret names
        """
        try:
            secrets = self.keyvault_client.list_properties_of_secrets()
            return [secret.name for secret in secrets]
        except Exception as e:
            logger.error(f"Error listing secrets: {e}")
            raise
