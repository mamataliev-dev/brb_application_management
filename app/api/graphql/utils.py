import logging
import uuid

from flask import session
from graphql import GraphQLError

from .types import Note, Application, Manager, Admin
from app.models import Application as ApplicationModel, Manager as ManagerModel

logger = logging.getLogger(__name__)


class NotesMapper:
    """Maps and processes notes data from RequestModel."""

    def map_notes(self, application):
        """
        Extracts and converts RequestModel.notes into a list of Note objects.

        Args:
            application (RequestModel): The request data containing notes.

        Returns:
            list[Note]: A list of Note objects, or an empty list if invalid/missing.
        """
        notes_data = self._extract_notes(application)

        if not notes_data:
            return []

        return self._map_notes(notes_data)

    def _extract_notes(self, application):
        """
        Safely extracts the notes attribute from request data.

        Args:
            application (RequestModel): The incoming request model.

        Returns:
            list[dict] | None: A list of note dictionaries if valid, else None.
        """
        if not hasattr(application, "notes"):
            logger.warning("RequestModel is missing 'notes' attribute.")
            return None

        if not isinstance(application.notes, list):
            logger.warning(f"Invalid notes format: {type(application.notes)}")
            return None

        return application.notes

    def _map_notes(self, notes):
        """
        Converts a list of note dictionaries into Note objects.

        Args:
            notes (list[dict]): The extracted list of note dictionaries.

        Returns:
            list[Note]: A list of properly mapped Note objects.
        """
        mapped_notes = []
        for note in notes:
            note_obj = self._create_note_safe(note)
            if note_obj:
                mapped_notes.append(note_obj)

        return mapped_notes

    def _create_note_safe(self, note):
        """
        Safely creates a Note object while handling errors.

        Args:
            note (dict): A dictionary containing note data.

        Returns:
            Note | None: A Note object if valid, else None.
        """
        try:
            return Note(
                id=note["id"] if "id" in note else str(uuid.uuid4()),
                text=note["text"],
                timestamp=note["timestamp"],
                is_updated=note.get("is_updated", False),
                created_by=note["created_by"],
                updated_by=note["updated_by"],
            )
        except KeyError as e:
            logger.error(f"Missing key in note data: {e}, data: {note}")
        except TypeError:
            logger.error(f"Invalid note format: {note}")

        return None


def _validate_id(id_value, entity_name):
    """
    Validates and converts an ID to an integer.

    Args:
        id_value (str | int): The ID to validate.
        entity_name (str): The entity type (e.g., "Application", "Manager") for error messages.

    Returns:
        int: The parsed integer ID.

    Raises:
        GraphQLError: If the ID is invalid.
    """
    try:
        return int(id_value)
    except ValueError:
        logger.error(f"Invalid {entity_name} ID format: {id_value}")
        raise GraphQLError(f"Invalid {entity_name} ID format. It must be an integer.")


def _check_authorization():
    user = session.get("user")

    if not user:
        logger.error("Unauthorized access attempt - No session found.")
        raise GraphQLError("Unauthorized access attempt - No session found.")

    return user.get("role")


def build_application_response(application):
    """
    Constructs an Application response object.

    Args:
        application (ManagerModel): The manager object.

    Returns:
        Application: The structured Application response.

    Raises:
        ValueError: If the application is None.
    """
    if application is None:
        logger.error("Attempted to build a response for a None application.")
        raise ValueError("Cannot build response for a None application.")

    notes_mapper = NotesMapper()
    notes = notes_mapper.map_notes(application)

    return Application(
        id=str(application.id),
        branch=application.branch_name,
        client_name=application.client_name,
        phone_number=application.phone_number,
        created_at=application.created_at.isoformat() if application.created_at else None,
        product=application.product,
        status=application.status,
        deleted_at=application.deleted_at.isoformat() if application.deleted_at else None,
        is_deleted=application.is_deleted,
        deleted_by=application.deleted_by,
        notes=notes,
        history=application.history,
    )


def get_application_by_id(id):
    """
    Retrieves an application by its ID from the database with role-based filtering.

    - Only Admin see all applications (is_deleted = True & False).
    - Managers see only active applications (is_deleted = False).

    Args:
        id (int): The application ID.

    Returns:
        ApplicationModel | None: The Application object if found, else None.

    Logs:
        - WARNING if no application is found.
    """
    if id is None:
        logger.error("Attempted to fetch an application with an invalid ID (None).")
        return None

    role = _check_authorization()

    query = ApplicationModel.query.filter(ApplicationModel.id == int(id))

    if role == "manager":
        query = query.filter(ApplicationModel.is_deleted == False)  # Managers can't see deleted applications

    application = query.first()

    if not application:
        logger.warning(f"Application with ID '{id}' not found.")
        return None

    return application


def fetch_application(application_id):
    """
    Fetches an Application by ID, handling validation and errors.

    Args:
        application_id (str | int): The ID of the application to fetch.

    Returns:
        ApplicationModel: The fetched application object.

    Raises:
        GraphQLError: If the ID is invalid or the application is not found.
    """
    parsed_id = _validate_id(application_id, "Application")

    application = get_application_by_id(parsed_id)
    if not application:
        logger.warning(f"Application ID {parsed_id} not found.")
        raise GraphQLError(f"Application with ID {parsed_id} not found.")

    return application


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
    parsed_id = _validate_id(manager_id, "Manager")

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
    )
