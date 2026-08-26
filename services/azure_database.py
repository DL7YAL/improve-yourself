"""Azure SQL Database and Cosmos DB services."""

import logging
from typing import Optional, List, Dict, Any
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosHttpResponseError
import pyodbc

logger = logging.getLogger(__name__)


class AzureSQLService:
    """Handle Azure SQL Database operations."""

    def __init__(self, server: str, database: str, username: str, password: str):
        self.connection_string = (
            f'Driver={{ODBC Driver 18 for SQL Server}};'
            f'Server=tcp:{server},1433;'
            f'Database={database};'
            f'Uid={username};'
            f'Pwd={password};'
            f'Encrypt=yes;'
            f'TrustServerCertificate=no;'
            f'Connection Timeout=30;'
        )

    def execute_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """Execute a SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Query results
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Number of affected rows
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error executing update: {e}")
            raise


class AzureCosmosService:
    """Handle Azure Cosmos DB operations."""

    def __init__(self, cosmos_client: CosmosClient, database_name: str, container_name: str):
        self.client = cosmos_client
        self.database_name = database_name
        self.container_name = container_name
        self.database = self.client.get_database_client(database_name)
        self.container = self.database.get_container_client(container_name)

    def create_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Create an item in Cosmos DB.

        Args:
            item: Item to create (must have 'id' and partition key)

        Returns:
            Created item
        """
        try:
            return self.container.create_item(body=item)
        except CosmosHttpResponseError as e:
            logger.error(f"Error creating item: {e}")
            raise

    def read_item(self, item_id: str, partition_key: str) -> Dict[str, Any]:
        """Read an item from Cosmos DB.

        Args:
            item_id: Item ID
            partition_key: Partition key value

        Returns:
            Item data
        """
        try:
            return self.container.read_item(item=item_id, partition_key=partition_key)
        except CosmosHttpResponseError as e:
            logger.error(f"Error reading item: {e}")
            raise

    def query_items(self, query: str, parameters: Optional[List] = None) -> List[Dict]:
        """Query items from Cosmos DB.

        Args:
            query: SQL-like query string
            parameters: Optional query parameters

        Returns:
            List of matching items
        """
        try:
            return list(self.container.query_items(
                query=query,
                parameters=parameters or []
            ))
        except CosmosHttpResponseError as e:
            logger.error(f"Error querying items: {e}")
            raise

    def upsert_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or update an item in Cosmos DB.

        Args:
            item: Item to upsert

        Returns:
            Upserted item
        """
        try:
            return self.container.upsert_item(body=item)
        except CosmosHttpResponseError as e:
            logger.error(f"Error upserting item: {e}")
            raise

    def delete_item(self, item_id: str, partition_key: str) -> None:
        """Delete an item from Cosmos DB.

        Args:
            item_id: Item ID
            partition_key: Partition key value
        """
        try:
            self.container.delete_item(item=item_id, partition_key=partition_key)
        except CosmosHttpResponseError as e:
            logger.error(f"Error deleting item: {e}")
            raise
