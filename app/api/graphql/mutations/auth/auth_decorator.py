from functools import wraps
from flask import session
import logging

logger = logging.getLogger(__name__)


def login_required(role=None):
    """
    Decorator to enforce authentication and role-based access control.

    Args:
        role (str | list[str], optional): Required role(s) to access the function. Defaults to None.

    Returns:
        function: The wrapped function with authentication checks.

    Raises:
        PermissionError: If the user is not authenticated or does not have the required role.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_data = session.get("user")

            if not user_data:
                logger.warning("Unauthorized access attempt - No admin session found.")
                raise PermissionError("Authentication required.")

            user_role = user_data.get("role")

            if role:
                allowed_roles = [role] if isinstance(role, str) else role
                if user_role not in allowed_roles:
                    logger.warning(f"Access denied for role: {user_role}. Required: {allowed_roles}")
                    raise PermissionError(f"Access requires role: {', '.join(allowed_roles)}")

            return func(*args, **kwargs)

        return wrapper

    return decorator
