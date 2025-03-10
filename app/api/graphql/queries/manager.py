import logging

from graphene import ObjectType, Field, ID

from app.api.graphql.mutations.auth.auth_decorator import login_required
from app.api.graphql.types import Manager
from app.api.graphql.utils import build_manager_response, fetch_manager

logger = logging.getLogger(__name__)


class ManagerQuery(ObjectType):
    """
    GraphQL Query class for fetching a Manager by ID.

    - Only Admin can see manager details

    Attributes:
        fetch_manager_by_id (Field): A GraphQL field to retrieve a manager by their ID.
    """

    fetch_manager_by_id = Field(Manager, id=ID(required=True, description="The unique manager ID."))

    @classmethod
    @login_required(role="admin")
    def resolve_fetch_manager_by_id(cls, root, info, id):
        """
        Resolves the query to fetch a Manager by ID.

        Args:
            root (Any): GraphQL root argument (unused).
            info (ResolveInfo): GraphQL resolver context.
            id (str | int): The manager ID.

        Returns:
            Manager: The structured manager response.

        Raises:
            GraphQLError: If the manager is not found or an error occurs.
        """
        manager = fetch_manager(id)

        return build_manager_response(manager)
