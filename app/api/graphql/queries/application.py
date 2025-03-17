import logging

from graphene import ObjectType, Field, ID

from app import redis_client
from app.api.graphql.mutations.auth.auth_decorator import login_required
from app.api.graphql.types import Application
from app.api.graphql.utils.application_utils import build_application_response, fetch_application
from app.api.graphql.utils.cache_utils import get_application_from_cache, cache_application_info, \
    deserialize_application_info

logger = logging.getLogger(__name__)


class ApplicationQuery(ObjectType):
    """
    GraphQL Query class for fetching an Application by its ID.

    Attributes:
        fetch_application_by_id (Field): A GraphQL field to retrieve an application by ID.
    """

    fetch_application_by_id = Field(Application, id=ID(required=True), description="The unique application ID.")

    @classmethod
    @login_required(role=["admin", "manager"])
    def resolve_fetch_application_by_id(cls, root, info, id):
        """
        Resolves the query to fetch an Application by ID.

        Args:
            root (ObjectType): Root of the GraphQL schema.
            info (ResolveInfo): GraphQL resolver context.
            id (str | int): The ID of the application.

        Returns:
            Application | None: The Application object if found, else None.

        Raises:
            ValueError: If the application_id is invalid.
        """
        # cache_key = f"application:{id}"
        #
        # cached_response = get_application_from_cache(cache_key)
        # if cached_response:
        #     return cached_response
        #
        # application = fetch_application(id)

        cache_key = f"application:{id}:info"
        application_data = redis_client.hgetall(cache_key)

        if application_data:
            logger.info(f"Cache hit for application info {id}")
            return Application(**deserialize_application_info(application_dict=application_data))

        application = fetch_application(id)

        cache_application_info(application)

        return build_application_response(application)
