"""Domain-level custom exceptions."""


class DomainException(Exception):
    """Base exception for all domain-level errors."""

    pass


class RepositoryError(DomainException):
    """Exception raised when a repository operation fails."""

    pass


class EntityNotFoundError(RepositoryError):
    """Exception raised when an entity is not found."""

    def __init__(self, entity_type: str, entity_id: str):
        """
        Initialize entity not found error.

        Args:
            entity_type: Type of the entity (e.g., 'Order').
            entity_id: ID of the entity that was not found.
        """
        super().__init__(f"{entity_type} with ID {entity_id} not found")
        self.entity_type = entity_type
        self.entity_id = entity_id


class DuplicateEntityError(RepositoryError):
    """Exception raised when attempting to create a duplicate entity."""

    def __init__(self, entity_type: str, field: str, value: str):
        """
        Initialize duplicate entity error.

        Args:
            entity_type: Type of the entity (e.g., 'Exchange').
            field: Field that caused the duplicate (e.g., 'name').
            value: Value that was duplicated.
        """
        super().__init__(f"{entity_type} with {field}='{value}' already exists")
        self.entity_type = entity_type
        self.field = field
        self.value = value
