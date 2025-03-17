import logging
from datetime import datetime

from flask import session
from graphene import Mutation, Field, ID, Boolean, String
from graphql import GraphQLError

from app.api.graphql.mutations.auth.auth_decorator import login_required
from app.api.graphql.types import Application, UpdateApplicationInput
from app.api.graphql.utils.application_utils import build_application_response, fetch_application
from app.api.graphql.utils.cache_utils import get_application_from_cache
from app.models import ApplicationHistory as ApplicationHistoryModel
from app.extensions import db

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
    @login_required(role=["admin", "manager"])
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

        # !!!! Cache Update Strategy (Pre-population)
        # cache_key = f"application:{id}"
        #
        # cached_response = get_application_from_cache(cache_key)
        # if cached_response:
        #     return cached_response
        # !!!! Cache Update Strategy (Pre-population)

        application = fetch_application(input.id)

        original_values = {
            "branch_name": application.branch_name,
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
            raise GraphQLError("Internal server error while updating application.")

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
        for field in ['client_name', 'phone_number', 'product', 'status', 'branch_name']:
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

        for field in ['client_name', 'phone_number', 'product', 'status', 'branch_name']:
            value = getattr(input, field, None)
            if value is not None and value != original_values[field]:
                updated_fields.append(field)
                new_values[field] = value

        if not updated_fields:
            logger.info(f"No changes detected for Application ID {application.id}. History log not created.")
            return None

        history = ApplicationHistoryModel(
            application_id=application.id,
            updated_fields=updated_fields,
            previous_values=str({field: original_values[field] for field in updated_fields}),
            new_values=str({field: new_values[field] for field in updated_fields})
        )
        db.session.add(history)


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
    @login_required(role=["admin", "manager"])
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

        user_data = session.get("user")
        user = user_data.get("name") if user_data else None

        application.deleted_at = datetime.utcnow()
        application.deleted_by = user
        application.is_deleted = True
        logger.debug(f"Soft-deleted application: {id}")

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit database session: {str(e)}")
            raise GraphQLError("Internal server error while deleting application.")

        return DeleteApplication(success=True, message=f"Application {id} soft-deleted")
