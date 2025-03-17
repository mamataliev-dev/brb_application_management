import logging

from graphql import GraphQLError

from app.api.graphql.types import Note, Application
from app.models import Application as ApplicationModel, Manager as ManagerModel
from app.api.graphql.utils.common_utils import NotesMapper, check_authorization, validate_id

logger = logging.getLogger(__name__)


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

    if not isinstance(application, dict):
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

    notes_data = application.get('notes', [])
    history_data = application.get('history', [])

    notes = [Note(**note) for note in notes_data]

    history = history_data

    return Application(
        id=application.get('id'),
        branch=application.get('branch'),
        client_name=application.get('client_name'),
        phone_number=application.get('phone_number'),
        created_at=application.get('created_at'),
        product=application.get('product'),
        status=application.get('status'),
        deleted_at=application.get('deleted_at'),
        is_deleted=application.get('is_deleted'),
        deleted_by=application.get('deleted_by'),
        notes=notes,
        history=history,
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

    role = check_authorization()

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
    parsed_id = validate_id(application_id, "Application")

    application = get_application_by_id(parsed_id)
    if not application:
        logger.warning(f"Application ID {parsed_id} not found.")
        raise GraphQLError(f"Application with ID {parsed_id} not found.")

    return application
