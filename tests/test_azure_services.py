"""Tests for Azure services integration."""

import unittest
from unittest.mock import Mock, patch, MagicMock

import pytest

pytest.importorskip("azure.identity", reason="Azure infrastructure tests require the explicit optional Azure SDK extras")

from config.azure_config import AzureConfig, AzureServices
from services.azure_storage import AzureStorageService
from services.azure_keyvault import AzureKeyVaultService


class TestAzureConfig(unittest.TestCase):
    """Test Azure configuration."""

    @patch.dict('os.environ', {
        'AZURE_SUBSCRIPTION_ID': 'test-sub',
        'AZURE_TENANT_ID': 'test-tenant',
        'AZURE_CLIENT_ID': 'test-client',
        'AZURE_CLIENT_SECRET': 'test-secret'
    })
    def test_config_initialization(self):
        """Test that configuration initializes with environment variables."""
        config = AzureConfig()
        self.assertEqual(config.subscription_id, 'test-sub')
        self.assertEqual(config.tenant_id, 'test-tenant')
        self.assertEqual(config.client_id, 'test-client')
        self.assertEqual(config.client_secret, 'test-secret')


class TestAzureStorageService(unittest.TestCase):
    """Test Azure Storage service."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_services = Mock(spec=AzureServices)
        self.mock_blob_client = Mock()
        self.mock_services.blob_service_client = self.mock_blob_client
        self.storage_service = AzureStorageService(self.mock_services)

    def test_upload_blob(self):
        """Test uploading a blob."""
        # Mock container and blob clients
        mock_container = Mock()
        mock_blob = Mock()
        mock_blob.url = 'https://example.blob.core.windows.net/container/blob.txt'

        self.mock_blob_client.get_container_client.return_value = mock_container
        mock_container.upload_blob.return_value = mock_blob

        # Test upload
        data = b'test data'
        url = self.storage_service.upload_blob('test-container', 'test.txt', data)

        self.assertEqual(url, 'https://example.blob.core.windows.net/container/blob.txt')
        mock_container.upload_blob.assert_called_once()

    def test_list_blobs(self):
        """Test listing blobs."""
        mock_container = Mock()
        mock_blob1 = Mock(name='blob1.txt')
        mock_blob2 = Mock(name='blob2.txt')

        self.mock_blob_client.get_container_client.return_value = mock_container
        mock_container.list_blobs.return_value = [mock_blob1, mock_blob2]

        blobs = self.storage_service.list_blobs('test-container')

        self.assertEqual(len(blobs), 2)


class TestAzureKeyVaultService(unittest.TestCase):
    """Test Azure Key Vault service."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_services = Mock(spec=AzureServices)
        self.mock_keyvault_client = Mock()
        self.mock_services.keyvault_client = self.mock_keyvault_client
        self.keyvault_service = AzureKeyVaultService(self.mock_services)

    def test_set_secret(self):
        """Test setting a secret."""
        self.mock_keyvault_client.set_secret.return_value = Mock()

        self.keyvault_service.set_secret('test-secret', 'secret-value')

        self.mock_keyvault_client.set_secret.assert_called_once_with(
            'test-secret', 'secret-value', tags=None
        )

    def test_get_secret(self):
        """Test retrieving a secret."""
        mock_secret = Mock()
        mock_secret.value = 'secret-value'
        self.mock_keyvault_client.get_secret.return_value = mock_secret

        value = self.keyvault_service.get_secret('test-secret')

        self.assertEqual(value, 'secret-value')
        self.mock_keyvault_client.get_secret.assert_called_once_with('test-secret')


if __name__ == '__main__':
    unittest.main()
