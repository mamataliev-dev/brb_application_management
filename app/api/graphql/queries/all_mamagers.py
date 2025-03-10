import logging

from graphene import ObjectType, List, Int

from app.api.graphql.types import Manager
from app.api.graphql.utils import build_manager_response
from app.models import Manager as ManagerModel
from app.api.graphql.mutations.auth.auth_decorator import login_required

logger = logging.getLogger(__name__)


class AllManagersQuery(ObjectType):
    """
    GraphQL Query class for fetching all managers.

    - Only Admin can see all managers

    Attributes:
        fetch_managers (List[Manager]): A GraphQL field to retrieve all managers.

    Methods:
        resolve_fetch_managers(root, info, limit=10):
            Resolves the query to fetch managers with optional pagination.
    """
    fetch_all_managers = List(Manager, limit=Int(default_value=10), offset=Int(default_value=0))

    @classmethod
    @login_required(role="admin")
    def resolve_fetch_all_managers(cls, root, info, limit=10, offset=0):
        """
       Resolves the query to fetch managers.

       Args:
           root (Any): GraphQL root argument (unused).
           info (ResolveInfo): GraphQL resolver context.
           limit (int): The maximum number of managers to return.
           offset (int): The number of managers to skip (for pagination).

       Returns:
           List[Manager] | None: A list of manager objects or None if no managers exist.

       Raises:
           GraphQLError: If an unexpected error occurs.
       """
        managers = ManagerModel.query.offset(offset).limit(limit).all()

        return [build_manager_response(manager) for manager in managers]
