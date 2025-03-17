import logging
import uuid

from flask import session
from graphql import GraphQLError

from app.api.graphql.types import Note

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


def validate_id(id_value, entity_name):
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


def check_authorization():
    user = session.get("user")

    if not user:
        logger.error("Unauthorized access attempt - No session found.")
        raise GraphQLError("Unauthorized access attempt - No session found.")

    return user.get("role")
