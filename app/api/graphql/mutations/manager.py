import logging

from graphene import Mutation, Field
from graphql import GraphQLError

from app.api.graphql.mutations.auth.encryption_utils import encrypt_password
from app.api.graphql.mutations.auth.auth_decorator import login_required
from app.api.graphql.types import Manager, UpdateManagerInput
from app.api.graphql.utils.manager_utils import build_manager_response, fetch_manager
from app.extensions import db

logger = logging.getLogger(__name__)


class UpdateManager(Mutation):
    """
    Handles updating a manager and returning the updated manager data.

    Attributes:
        Arguments:
            input (UpdateManagerInput): Required input containing manager updates.
        manager (Field): Returns the updated Manager object.
    """

    class Arguments:
        input = UpdateManagerInput(required=True)

    manager = Field(Manager)

    @classmethod
    @login_required(role=["admin"])
    def mutate(cls, root, info, input):
        """
        Handles the mutation for updating a manager.

        Args:
            root (Any): Unused root argument for GraphQL.
            info (ResolveInfo): GraphQL resolver context.
            input (UpdateManagerInput): Input containing manager update details.

        Returns:
            UpdateManager: Updated manager response.

        Raises:
            GraphQLError: If the manager ID is not found or update fails.
        """
        manager = fetch_manager(input.id)

        cls._update_manager(manager, input)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit database session: {str(e)}")
            raise GraphQLError("Internal server error while updating manager.")

        return UpdateManager(manager=build_manager_response(manager))

    @classmethod
    def _update_manager(cls, manager, input):
        """
        Updates a manager's attributes based on input data.

        Args:
            manager (ManagerModel): The manager instance to be updated.
            input (UpdateManagerInput): Input containing update details.

        Returns:
            None
        """
        for field in ['name', 'branch_name']:
            value = getattr(input, field, None)
            if value is not None:
                setattr(manager, field, value)

        if input.password:
            manager.password = encrypt_password(input.password)
