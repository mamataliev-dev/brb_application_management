import logging
import uuid

from flask import session
from graphene import Mutation, Field, ID
from graphql import GraphQLError
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime

from app.api.graphql.mutations.auth.auth_decorator import login_required
from app.api.graphql.types import Application, NoteInput
from app.api.graphql.utils.application_utils import build_application_response, fetch_application
from app.extensions import db

logger = logging.getLogger(__name__)


class AddNoteToApplication(Mutation):
    """
    GraphQL Mutation to add a note to an existing application.

    Attributes:
       Arguments:
           id (ID): The unique application ID.
           note (NoteInput): The note object containing text and timestamp.
       application (Field): The updated Application object.
    """

    class Arguments:
        id = ID(required=True)
        note = NoteInput(required=True)

    application = Field(Application)

    @classmethod
    @login_required(role=["admin", "manager"])
    def mutate(cls, root, info, id, note):
        """
        Adds a note to the specified application.

        Args:
            root (Any): GraphQL root argument (unused).
            info (ResolveInfo): GraphQL resolver context.
            id (str | int): The application ID.
            note (NoteInput): The note containing text and timestamp.

        Returns:
            AddNoteToApplication: Mutation response with updated application.

        Raises:
            GraphQLError: If the ID is invalid, the application is not found,
                          or if the database fails to commit.
        """
        application = fetch_application(id)

        user_data = session.get("user")
        user = user_data.get("name")

        if not isinstance(application.notes, list):
            application.notes = []

        new_note = {
            "id": str(uuid.uuid4()),
            "text": note.text,
            "timestamp": datetime.utcnow().isoformat(),
            "is_updated": False,
            "created_by": user,
            "updated_by": None
        }

        application.notes.append(new_note)

        flag_modified(application, "notes")

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit database session: {str(e)}")
            raise GraphQLError("Internal server error while adding note to application.")

        return AddNoteToApplication(application=build_application_response(application))


class RemoveNoteFromApplication(Mutation):
    """
    GraphQL Mutation to remove a note from an existing application.

    Attributes:
       Arguments:
           id (ID): The unique application ID.
           note_id (ID): The unique ID of the note to be removed.
       application (Field): The updated Application object.
    """

    class Arguments:
        id = ID(required=True, description="The unique application ID.")
        note_id = ID(required=True, description="The unique ID of the note to remove.")

    application = Field(Application)

    @classmethod
    @login_required(role=["admin", "manager"])
    def mutate(cls, root, info, id, note_id):
        """
        Removes a note from the specified application.

        Args:
            root (Any): GraphQL root argument (unused).
            info (ResolveInfo): GraphQL resolver context.
            id (str): The application ID.
            note_id (str): The ID of the note to be removed.

        Returns:
            RemoveNoteFromApplication: Mutation response with the updated application.

        Raises:
            GraphQLError: If the application ID is not found,
                          the note ID is missing in the application,
                          or if the database fails to commit.
        """
        application = fetch_application(id)
        if not application:
            logger.warning(f"Application with ID {id} not found.")
            raise GraphQLError(f"Application with ID {id} not found.")

        cls._remove_note(application, note_id)

        flag_modified(application, "notes")

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit database session: {str(e)}")
            raise GraphQLError("Internal server error while removing note from application.")

        return RemoveNoteFromApplication(application=build_application_response(application))

    @classmethod
    def _remove_note(cls, application, note_id):
        """
        Safely removes a note from the application.

        Args:
            application (ApplicationModel): The application instance.
            note_id (str): The unique ID of the note to remove.

        Raises:
            GraphQLError: If the note is not found in the application.
        """
        if not isinstance(application.notes, list):
            application.notes = []

        note_to_remove = next((n for n in application.notes if n.get("id") == note_id), None)
        if not note_to_remove:
            logger.warning(f"Note with ID {note_id} not found in application {application.id}")
            raise GraphQLError(f"Note with ID {note_id} not found in application {application.id}.")

        application.notes[:] = [n for n in application.notes if n.get("id") != note_id]


class UpdateNoteFromApplication(Mutation):
    """
    GraphQL Mutation to add a note to an existing application.

    Attributes:
       Arguments:
           id (ID): The unique application ID.
           note (NoteInput): The note object containing text and timestamp.
       application (Field): The updated Application object.
    """

    class Arguments:
        id = ID(required=True, description="The application ID")
        note_id = ID(required=True, description="ID of the note to update")
        new_note = NoteInput(required=True)

    application = Field(Application)

    @classmethod
    @login_required(role=["admin", "manager"])
    def mutate(cls, root, info, id, note_id, new_note):
        """
        Adds a note to the specified application.

        Args:
            root (Any): GraphQL root argument (unused).
            info (ResolveInfo): GraphQL resolver context.
            id (str | int): The application ID.
            note (NoteInput): The note containing text and timestamp.

        Returns:
            AddNoteToApplication: Mutation response with updated application.

        Raises:
            GraphQLError: If the ID is invalid, the application is not found,
                          or if the database fails to commit.
        """
        application = fetch_application(id)

        cls._update_note(application, note_id, new_note)

        flag_modified(application, "notes")

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit database session: {str(e)}")
            raise GraphQLError("Internal server error while updating note from application.")

        return UpdateNoteFromApplication(application=build_application_response(application))

    @classmethod
    def _update_note(cls, application, note_id, new_note):
        note_to_update = next((n for n in application.notes if n.get("id") == note_id), None)

        user_data = session.get("user")
        user = user_data.get("name")

        if not note_to_update:
            logger.warning(f"Note with ID {note_id} not found in application {application.id}")
            raise GraphQLError(f"Note with ID {note_id} not found in application {application.id}.")

        if new_note.text is not None:
            note_to_update["text"] = new_note.text
            note_to_update["is_updated"] = True
            note_to_update["updated_by"] = user
