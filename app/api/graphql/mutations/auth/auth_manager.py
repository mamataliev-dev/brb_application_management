import logging
import uuid

from flask import session
from graphene import Mutation, Field, ID, Boolean, String
from graphql import GraphQLError

from .encryption_utils import decrypt_password, encrypt_password
from app.api.graphql.mutations.auth.auth_decorator import login_required
from app.api.graphql.types import Manager
from app.api.graphql.utils import fetch_manager
from app.extensions import db
from app.models import Manager as ManagerModel

logger = logging.getLogger(__name__)


class RegisterManager(Mutation):
    """
    GraphQL Mutation to register a new manager.

    - Only Admin can register manager

    Attributes:
        Arguments:
            name (str): The manager's name.
            password (str): The manager's password.
        manager (Field): The created Manager object.
    """

    class Arguments:
        name = String(required=True, description="The name of the manager.")
        password = String(required=True, description="The manager's password.")
        branch = String(required=True, description="The branch of the manager.")

    manager = Field(Manager)

    @classmethod
    @login_required(role="admin")
    def mutate(cls, root, info, name, password, branch):
        """
        Handles manager registration.

        Args:
            root (Any): GraphQL root argument (unused).
            info (ResolveInfo): GraphQL resolver context.
            name (str): The manager's name.
            password (str): The manager's raw password.
            branch (str): The branch of the manager.

        Returns:
            RegisterManager: Mutation response with the created manager.

        Raises:
            GraphQLError: If validation fails or database errors occur.
        """
        name, password, branch = cls._validate_data(name, password, branch)
        username = cls._generate_short_uuid()

        hashed_password = encrypt_password(password)

        new_manager = ManagerModel(username=username, name=name, password=hashed_password, branch_name=branch)

        db.session.add(new_manager)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit database session: {str(e)}")
            raise GraphQLError("Internal server error while registering manager.")

        logger.info(f"Manager {name} registered successfully.")
        return RegisterManager(manager=new_manager)

    @classmethod
    def _validate_data(cls, name, password, branch):
        """
        Validates manager input data.

        Args:
            name (str): The manager's name.
            password (str): The manager's password.

        Returns:
            tuple: Validated (name, password).

        Raises:
            GraphQLError: If input data is missing or invalid.
        """
        if not name:
            raise GraphQLError("Manager name is required.")

        if not password:
            raise GraphQLError("Manager password is required.")

        if not branch:
            raise GraphQLError("Manager branch is required.")

        return name, password, branch

    @classmethod
    def _generate_short_uuid(cls):
        return uuid.uuid4().hex[:8]


class LoginManager(Mutation):
    """
    GraphQL Mutation for manager login.

    Attributes:
        Arguments:
            username (str): The manager's name.
            password (str): The manager's password.
        manager (Field): The authenticated manager object.
    """

    class Arguments:
        username = String(required=True, description="The username of the manager.")
        password = String(required=True, description="The manager's password.")

    manager = Field(Manager)

    @classmethod
    def mutate(cls, root, info, username, password):
        """
        Authenticates a manager and stores session data.

        Args:
            root (Any): GraphQL root argument (unused).
            info (ResolveInfo): GraphQL resolver context.
            username (str): The manager's name.
            password (str): The raw password provided by the user.

        Returns:
            LoginManager: Mutation response with the authenticated manager.

        Raises:
            GraphQLError: If the manager is not found, password is incorrect,
                          or a database error occurs.
        """
        manager = cls._fetch_manager_by_username(username)

        stored_encrypted_password = manager.password

        try:
            decrypted_stored_password = decrypt_password(stored_encrypted_password)
            if decrypted_stored_password != password:
                logger.warning(f"Login failed: Invalid password for Manager '{username}'.")
                raise GraphQLError("Invalid credentials.")
        except Exception as e:
            logger.error(f"Decryption failed for '{username}': {str(e)}")
            raise GraphQLError("Invalid credentials (password decryption error).")

        session["user"] = {"id": manager.id, "name": manager.name, "role": "manager"}

        logger.info(f"Manager '{username}' logged in successfully.")
        return LoginManager(manager=manager)

    @classmethod
    def _fetch_manager_by_username(cls, username):
        """
        Fetches a manager by their username.

        Args:
            username (str): The username of the manager.

        Returns:
            ManagerModel: The Manager object if found.

        Raises:
            GraphQLError: If the manager does not exist or invalid credentials are provided.
            ValueError: If the provided username is empty or None.

        Logs:
            - WARNING if the manager is not found.
            - ERROR if a database issue occurs.
        """
        if not username or not isinstance(username, str):
            logger.warning("Login failed: Username is missing or invalid.")
            raise ValueError("Username cannot be empty or null.")

        try:
            manager = ManagerModel.query.filter_by(username=username).first()
        except Exception as e:
            logger.error(f"Database error while fetching manager '{username}': {str(e)}")
            raise GraphQLError("Internal server error. Please try again later.")

        if not manager:
            logger.warning(f"Login failed: Manager '{username}' not found.")
            raise GraphQLError("Manager not found.")

        return manager


class LogoutManager(Mutation):
    """
    GraphQL Mutation for logging out a user.

    Attributes:
        success (Boolean): Indicates if logout was successful.
        message (String): Message regarding the logout status.

    Methods:
        mutate(info): Handles session logout.
    """

    success = Boolean()
    message = String()

    def mutate(self, info):
        """
        Handles user logout by clearing session data.

        Args:
            info (ResolveInfo): GraphQL resolver context.

        Returns:
            LogoutUser: Mutation response indicating success or failure.
        """
        if "user" in session:
            session.pop("user")

            return LogoutManager(success=True, message="Logout successful.")

        return LogoutManager(success=False, message="No active session found.")


class DeleteManager(Mutation):
    """
    GraphQL Mutation to delete a manager.

    - Only Admin can delete manager

    Attributes:
        Arguments:
            id (ID): The unique ID of the manager.
        success (Boolean): Indicates if the deletion was successful.
        message (String): A message regarding the deletion status.
    """

    class Arguments:
        id = ID(required=True, description="The id of the manager.")

    success = Boolean()
    message = String()

    @classmethod
    @login_required(role="admin")
    def mutate(cls, root, info, id):
        """
        Deletes a manager from the system.

        Args:
            root (Any): GraphQL root argument (unused).
            info (ResolveInfo): GraphQL resolver context.
            id (str | int): The ID of the manager to delete.

        Returns:
            DeleteManager: Mutation response indicating success or failure.

        Raises:
            GraphQLError: If the manager is not found or a database error occurs.
        """
        manager = fetch_manager(id)

        if not manager:
            logger.warning(f"Attempted to delete a non-existent manager with ID {id}.")
            return DeleteManager(success=False, message=f"Manager with ID {id} not found.")

        db.session.delete(manager)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit database session: {str(e)}")
            raise GraphQLError("Internal server error while deleting manager.")

        logger.info(f"Manager ID {id} deleted successfully.")
        return DeleteManager(success=True, message=f"Manager with ID {id} deleted successfully.")
