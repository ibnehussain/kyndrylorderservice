"""Base repository pattern implementation"""

from abc import ABC, abstractmethod
from typing import Dict, Generic, List, Optional, TypeVar

from azure.cosmos import ContainerProxy, CosmosClient, DatabaseProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.core.config import get_settings

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository class"""

    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[CosmosClient] = None
        self._database: Optional[DatabaseProxy] = None
        self._container: Optional[ContainerProxy] = None

    @property
    def client(self) -> CosmosClient:
        """Get or create Cosmos client"""
        if not self._client:
            self._client = CosmosClient(
                self.settings.effective_cosmos_endpoint,
                self.settings.effective_cosmos_key,
            )
        return self._client

    @property
    def database(self) -> DatabaseProxy:
        """Get or create database"""
        if not self._database:
            self._database = self.client.get_database_client(
                self.settings.cosmos_database
            )
        return self._database

    @property
    def container(self) -> ContainerProxy:
        """Get or create container"""
        if not self._container:
            self._container = self.database.get_container_client(
                self.settings.cosmos_container
            )
        return self._container

    async def create_database_if_not_exists(self) -> None:
        """Create database if it doesn't exist"""
        try:
            self.client.create_database(self.settings.cosmos_database)
        except:
            pass  # Database already exists

    async def create_container_if_not_exists(self) -> None:
        """Create container if it doesn't exist"""
        try:
            self.database.create_container(
                id=self.settings.cosmos_container,
                partition_key="/partitionKey",
                offer_throughput=400,
            )
        except:
            pass  # Container already exists

    @abstractmethod
    async def create(self, item: T) -> T:
        """Create a new item"""
        pass

    @abstractmethod
    async def get_by_id(self, item_id: str, partition_key: str) -> Optional[T]:
        """Get item by ID and partition key"""
        pass

    @abstractmethod
    async def update(self, item: T) -> T:
        """Update an existing item"""
        pass

    @abstractmethod
    async def delete(self, item_id: str, partition_key: str) -> bool:
        """Delete an item"""
        pass

    @abstractmethod
    async def list_items(
        self, partition_key: Optional[str] = None, max_items: int = 100, offset: int = 0
    ) -> List[T]:
        """List items with pagination"""
        pass


class DatabaseManager:
    """Database initialization and management"""

    def __init__(self):
        self.settings = get_settings()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize database and containers"""
        if self._initialized:
            return

        try:
            client = CosmosClient(
                self.settings.effective_cosmos_endpoint,
                self.settings.effective_cosmos_key,
            )

            # Create database
            try:
                client.create_database(self.settings.cosmos_database)
                print(f"Created database: {self.settings.cosmos_database}")
            except:
                print(f"Database {self.settings.cosmos_database} already exists")

            # Get database client
            database = client.get_database_client(self.settings.cosmos_database)

            # Create container
            try:
                database.create_container(
                    id=self.settings.cosmos_container,
                    partition_key="/partitionKey",
                    offer_throughput=400,
                )
                print(f"Created container: {self.settings.cosmos_container}")
            except:
                print(f"Container {self.settings.cosmos_container} already exists")

            self._initialized = True
            print("Database initialization completed successfully")

        except Exception as e:
            print(f"Database initialization failed: {e}")
            raise


# Global database manager instance
db_manager = DatabaseManager()
