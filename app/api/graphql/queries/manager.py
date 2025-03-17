import logging

from graphene import ObjectType, Field, ID

from app.api.graphql.mutations.auth.auth_decorator import login_required
from app.api.graphql.types import Manager
from app.api.graphql.utils.manager_utils import build_manager_response, fetch_manager
from app.api.graphql.utils.cache_utils import get_manager_from_cache

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
        cache_key = f"manager:{id}"

        # TODO: Change manager redis data structure to hash-tables

        cached_response = get_manager_from_cache(cache_key)
        if cached_response:
            return cached_response

        manager = fetch_manager(id)

        return build_manager_response(manager)
