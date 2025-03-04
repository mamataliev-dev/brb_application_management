import logging

from graphene import ObjectType, Field, ID
from app.api.graphql.types import Application
from app.api.graphql.utils import build_application_response, fetch_application

logger = logging.getLogger(__name__)


class ApplicationQuery(ObjectType):
    """
    GraphQL Query class for fetching an Application by its ID.

    Attributes:
        fetch_by_id (Field): A GraphQL field to retrieve an application by ID.
    """

    fetch_application_by_id = Field(Application, id=ID(required=True))

    @classmethod
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
        application = fetch_application(id)

        return build_application_response(application)
