import pytest
from graphene.test import Client
from flask import session
from app.api.graphql.schema import schema
from app.models import db, Admin
from app import create_app


@pytest.fixture
def test_app():
    """Fixture to create a test app instance."""
    app = create_app()
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(test_app):
    """GraphQL client for testing."""
    return Client(schema)


@pytest.fixture
def sample_admin(test_app):
    """Creates a sample admin in the test database."""
    with test_app.app_context():
        admin = Admin(id=1, name="admin", password=encrypt_password("securepassword"))
        db.session.add(admin)
        db.session.commit()
        return admin


def test_admin_login_success(client, test_app, sample_admin):
    """Test that an admin can log in successfully."""
    with test_app.test_request_context():
        query = """
        mutation {
          loginAdmin(password: "securepassword") {
            success
            message
            admin {
              id
              name
            }
          }
        }
        """

        response = client.execute(query)
        data = response.get("data", {}).get("loginAdmin", {})

        assert response is not None
        assert "errors" not in response
        assert data["success"] is True
        assert data["message"] == "Admin login successful"
        assert data["admin"]["name"] == "admin"


def test_admin_login_invalid_password(client, test_app, sample_admin):
    """Test that login fails with an incorrect password."""
    with test_app.test_request_context():
        query = """
        mutation {
          loginAdmin(password: "wrongpassword") {
            success
            message
            admin {
              id
              name
            }
          }
        }
        """

        response = client.execute(query)

        assert response is not None
        assert "errors" in response
        assert "Invalid credentials." in response["errors"][0]["message"]


def test_admin_login_no_admin(client, test_app):
    """Test that login fails when no admin exists in the database."""
    with test_app.test_request_context():
        query = """
        mutation {
          loginAdmin(password: "securepassword") {
            success
            message
            admin {
              id
              name
            }
          }
        }
        """

        response = client.execute(query)

        assert response is not None
        assert "errors" in response
        assert "Invalid credentials." in response["errors"][0]["message"]
