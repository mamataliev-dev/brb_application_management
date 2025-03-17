import logging

from graphql import GraphQLError

from app.api.graphql.types import Manager
from app.models import Manager as ManagerModel

from app.api.graphql.utils.common_utils import validate_id

logger = logging.getLogger(__name__)


def get_manager_by_id(manager_id):
    """
    Fetches a Manager by ID.

    - Only Admin can see manager details.

    Args:
        manager_id (int): The ID of the manager.

    Returns:
        ManagerModel | None: The manager object if found, otherwise None.
    """
    if not manager_id:
        logger.error("Attempted to fetch a manager with an invalid ID (None).")
        return None

    manager = ManagerModel.query.filter(
        ManagerModel.id == int(manager_id)).first()  # Only Admin can see manager details

    if not manager:
        logger.warning(f"Manager with ID '{manager_id}' not found.")
        return None

    return manager


def fetch_manager(manager_id):
    """
    Fetches a Manager by ID, handling validation and errors.

    Args:
        manager_id (str | int): The ID of the manager to fetch.

    Returns:
        ManagerModel: The fetched manager object.

    Raises:
        GraphQLError: If the ID is invalid or the manager is not found.
    """
    parsed_id = validate_id(manager_id, "Manager")

    manager = get_manager_by_id(parsed_id)
    if not manager:
        logger.warning(f"Manager ID {parsed_id} not found.")
        raise GraphQLError(f"Manager with ID {parsed_id} not found.")

    return manager


def build_manager_response(manager):
    """
    Constructs a Manager response object.

    Args:
        manager (ManagerModel): The manager object.

    Returns:
        Manager: The structured Manager response.

    Raises:
        ValueError: If the manager is None.
    """
    if manager is None:
        logger.error("Attempted to build a response for a None manager.")
        raise ValueError("Cannot build response for a None manager.")

    return Manager(
        id=manager.id,
        username=manager.username,
        name=manager.name,
        branch=manager.branch_name,
        created_at=manager.created_at.isoformat() if manager.created_at else None,
        password=manager.password
    )
