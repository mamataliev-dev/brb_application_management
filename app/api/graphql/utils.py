import logging
import uuid

from graphql import GraphQLError

from .types import Note, Application
from app.models import Application as ApplicationModel, db

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
            )
        except KeyError as e:
            logger.error(f"Missing key in note data: {e}, data: {note}")
        except TypeError:
            logger.error(f"Invalid note format: {note}")

        return None


def build_application_response(application):
    notes_mapper = NotesMapper()
    notes = notes_mapper.map_notes(application)

    return Application(
        id=str(application.id),
        branch_id=application.branch_id,
        client_name=application.client_name,
        phone_number=application.phone_number,
        created_at=application.created_at.isoformat() if application.created_at else None,
        product=application.product,
        status=application.status,
        notes=notes,
        history_entries=application.history_entries,
        deleted_at=application.deleted_at.isoformat() if application.deleted_at else None,
        is_deleted=application.is_deleted,
    )


def get_application_by_id(id):
    """
    Retrieves an application by its ID from the database.

    Args:
        id (int): The application ID.

    Returns:
        RequestModel | None: The Application object if found, else None.

    Logs:
        - WARNING if no application is found.
    """
    if id is None:
        logger.error("Attempted to fetch an application with an invalid ID (None).")
        return None

    application = ApplicationModel.query.filter(
        (ApplicationModel.id == int(id)) & (ApplicationModel.is_deleted == False)
    ).first()

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
    try:
        parsed_id = int(application_id)
    except ValueError:
        logger.error(f"Invalid application ID format: {application_id}")
        raise GraphQLError("Invalid application ID format.")

    application = get_application_by_id(application_id)
    if not application:
        logger.warning(f"Application ID {parsed_id} not found")
        raise GraphQLError(f"Application with ID {parsed_id} not found.")

    return application
