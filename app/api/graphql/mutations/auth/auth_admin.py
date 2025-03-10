import logging

from flask import session
from graphene import Mutation, Field, Boolean, String
from graphql import GraphQLError

from app.models import Admin as AdminModel
from app.api.graphql.types import Admin
from .encryption_utils import decrypt_password, encrypt_password

logger = logging.getLogger(__name__)


class LoginAdmin(Mutation):
    """
    GraphQL Mutation for admin login.

    Attributes:
        Arguments:
            password (String): The admin's password.
        success (Boolean): Indicates if the login was successful.
        message (String): Message regarding the login status.
        admin (Field): The authenticated admin object.
    """

    class Arguments:
        password = String(required=True, description="The admin's password.")

    success = Boolean()
    message = String()
    admin = Field(Admin)

    @classmethod
    def mutate(cls, root, info, password):
        """
        Authenticates an admin and starts a session.

        Args:
            root (Any): GraphQL root argument (unused).
            info (ResolveInfo): GraphQL resolver context.
            password (str): The raw password provided by the admin.

        Returns:
            LoginAdmin: Mutation response with success status and authenticated admin.

        Raises:
            GraphQLError: If the admin is not found, password is incorrect,
                          or an unexpected error occurs.
        """
        admin = AdminModel.query.first()

        if not admin:
            logger.warning("Admin login attempt failed: No admin found in the database.")
            raise GraphQLError("Invalid credentials.")

        decrypted_password = decrypt_password(admin.password)

        if decrypted_password != password:
            logger.warning("Admin login attempt failed: Incorrect password.")
            raise GraphQLError("Invalid credentials.")

        session["user"] = {"name": "admin", "role": "admin"}

        logger.info("Admin logged in successfully.")
        return LoginAdmin(success=True, message="Admin login successful", admin=admin)
