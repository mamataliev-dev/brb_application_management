import logging
from datetime import datetime

from graphene import Mutation, Field, ID, Boolean, String
from graphql import GraphQLError
from sqlalchemy.orm.attributes import flag_modified

from app.api.graphql.types import Application, UpdateApplicationInput, NoteInput
from app.api.graphql.utils import build_application_response, fetch_application
from app.extensions import db
from app.models import ApplicationHistory as ApplicationHistoryModel

logger = logging.getLogger(__name__)


class UpdateApplication(Mutation):
    """
    Handles updating an application and returning the updated application data.

    Attributes:
        Arguments:
            input (UpdateApplicationInput): Required input containing application updates.
        application (Field): Returns the updated Application object.
    """

    class Arguments:
        input = UpdateApplicationInput(required=True)

    application = Field(Application)

    @classmethod
    def mutate(cls, root, info, input):
        """
        Handles the mutation for updating an application.

        Args:
            root (Any): Unused root argument for GraphQL.
            info (ResolveInfo): GraphQL resolver context.
            input (UpdateApplicationInput): Input containing application update details.
            builder (ApplicationResponseBuilder, optional): Instance of response builder for dependency injection.

        Returns:
            UpdateApplication: Updated application response.

        Raises:
            GraphQLError: If the application ID is not found.
        """
        application = fetch_application(input.id)

        original_values = {
            "branch_id": application.branch_id,
            "client_name": application.client_name,
            "phone_number": application.phone_number,
            "product": application.product,
            "status": application.status,
        }

        cls._update_application(application, input)
        cls._add_updated_field_to_history(application, input, original_values)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit database session: {str(e)}")
            raise GraphQLError("Internal server error while saving the application.")

        return UpdateApplication(application=build_application_response(application))

    @classmethod
    def _update_application(cls, application, input):
        """
       Updates an application's attributes based on input data.

       Args:
           application (ApplicationModel): The application instance to be updated.
           input (UpdateApplicationInput): Input containing update details.

       Returns:
           None
       """
        if input.branch_id is not None:
            application.branch_id = int(input.branch_id)

        for field in ['client_name', 'phone_number', 'product', 'status']:
            value = getattr(input, field, None)
            if value is not None:
                setattr(application, field, value)

    @classmethod
    def _add_updated_field_to_history(cls, application, input, original_values):
        """
        Tracks changes made to an application and stores them in the history log.

        Args:
            application (ApplicationModel): The updated application.
            input (UpdateApplicationInput): The new input data.
            original_values (dict): The original application data before updates.

        Returns:
            ApplicationHistoryModel | None: History entry if created, otherwise None.

        Logs:
            - INFO if no changes were detected.
        """
        updated_fields = []
        new_values = {}

        if input.branch_id is not None and input.branch_id != str(original_values["branch_id"]):
            updated_fields.append("branch_id")
            new_values["branch_id"] = input.branch_id

        for field in ['client_name', 'phone_number', 'product', 'status']:
            value = getattr(input, field, None)
            if value is not None and value != original_values[field]:
                updated_fields.append(field)
                new_values[field] = value

        if not updated_fields:
            logger.info(f"No changes detected for Application ID {application.id}. History log not created.")
            return None

        history_entry = ApplicationHistoryModel(
            application_id=application.id,
            updated_fields=updated_fields,
            previous_values=str({field: original_values[field] for field in updated_fields}),
            new_values=str({field: new_values[field] for field in updated_fields})
        )

        db.session.add(history_entry)


class DeleteApplication(Mutation):
    """
    Handles deletion of an application.

    Attributes:
        Arguments:
            id (ID): The unique ID of the application to be deleted.
        success (Boolean): Indicates whether the deletion was successful.
        message (String): A status message regarding the deletion.
    """

    class Arguments:
        id = ID(required=True)

    success = Field(Boolean)
    message = Field(String)

    @classmethod
    def mutate(cls, root, info, id):
        """
        Soft-deletes an application by setting deleted_at.

        Args:
            root (Any): Unused root argument for GraphQL.
            info (ResolveInfo): GraphQL resolver context.
            id (str): The application ID to soft-delete.

        Returns:
            DeleteApplication: Success status and message.

        Raises:
            GraphQLError: If the application ID is not found or commit fails.
        """
        application = fetch_application(id)

        application.deleted_at = datetime.utcnow()
        application.is_deleted = True
        logger.debug(f"Soft-deleted application: {id}")

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit database session: {str(e)}")
            raise GraphQLError("Internal server error while soft-deleting the application.")

        return DeleteApplication(success=True, message=f"Application {id} soft-deleted")


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

        if not isinstance(application.notes, list):
            application.notes = []

        application.notes.append({"text": note.text, "timestamp": note.timestamp})

        flag_modified(application, "notes")

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit database session: {str(e)}")
            raise GraphQLError("Internal server error while saving the application.")

        return AddNoteToApplication(application=build_application_response(application))
