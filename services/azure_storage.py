"""Azure Blob Storage service."""

import logging
from typing import Optional, BinaryIO
from azure.storage.blob import BlobClient, ContainerClient
from config.azure_config import AzureServices

logger = logging.getLogger(__name__)


class AzureStorageService:
    """Handle Azure Blob Storage operations."""

    def __init__(self, azure_services: AzureServices):
        self.blob_client = azure_services.blob_service_client

    def upload_blob(self, container_name: str, blob_name: str, data: BinaryIO) -> str:
        """Upload a blob to Azure Storage.

        Args:
            container_name: Name of the storage container
            blob_name: Name of the blob
            data: File-like object to upload

        Returns:
            URL of uploaded blob
        """
        try:
            container_client = self.blob_client.get_container_client(container_name)
            blob_client = container_client.upload_blob(blob_name, data, overwrite=True)
            logger.info(f"Blob uploaded: {blob_name} to {container_name}")
            return blob_client.url
        except Exception as e:
            logger.error(f"Error uploading blob: {e}")
            raise

    def download_blob(self, container_name: str, blob_name: str) -> bytes:
        """Download a blob from Azure Storage.

        Args:
            container_name: Name of the storage container
            blob_name: Name of the blob

        Returns:
            Blob data as bytes
        """
        try:
            container_client = self.blob_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)
            return blob_client.download_blob().readall()
        except Exception as e:
            logger.error(f"Error downloading blob: {e}")
            raise

    def list_blobs(self, container_name: str, prefix: Optional[str] = None) -> list:
        """List blobs in a container.

        Args:
            container_name: Name of the storage container
            prefix: Optional prefix to filter results

        Returns:
            List of blob names
        """
        try:
            container_client = self.blob_client.get_container_client(container_name)
            blobs = container_client.list_blobs(name_starts_with=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            logger.error(f"Error listing blobs: {e}")
            raise

    def delete_blob(self, container_name: str, blob_name: str) -> None:
        """Delete a blob from Azure Storage.

        Args:
            container_name: Name of the storage container
            blob_name: Name of the blob
        """
        try:
            container_client = self.blob_client.get_container_client(container_name)
            container_client.delete_blob(blob_name)
            logger.info(f"Blob deleted: {blob_name} from {container_name}")
        except Exception as e:
            logger.error(f"Error deleting blob: {e}")
            raise

    def create_container(self, container_name: str) -> None:
        """Create a new container.

        Args:
            container_name: Name of the container to create
        """
        try:
            self.blob_client.create_container(name=container_name)
            logger.info(f"Container created: {container_name}")
        except Exception as e:
            logger.error(f"Error creating container: {e}")
            raise
