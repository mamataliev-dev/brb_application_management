import pytest
from graphene.test import Client
from flask import session
from app.api.graphql.schema import schema
from app.models import db, Manager, Admin, Branch
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


@pytest.fixture
def sample_manager(test_app):
    """Creates a sample manager in the test database."""
    with test_app.app_context():
        branch = Branch(name="Test Branch")
        db.session.add(branch)
        db.session.commit()

        manager = Manager(id=1, username="test_manager", name="John Doe", password=encrypt_password("password"),
                          branch_name="Test Branch")
        db.session.add(manager)
        db.session.commit()
        return manager


def test_register_manager_as_admin(client, test_app, sample_admin):
    """Test that an admin can register a new manager."""
    with test_app.test_request_context():
        session["user"] = {"role": "admin"}

        query = """
        mutation {
          registerManager(name: "New Manager", password: "newpassword", branch: "Test Branch") {
            manager {
              name
              branch
            }
          }
        }
        """

        response = client.execute(query)
        data = response.get("data", {}).get("registerManager", {}).get("manager", {})

        assert response is not None
        assert "errors" not in response
        assert data["name"] == "New Manager"
        assert data["branch"] == "Test Branch"


def test_register_manager_as_non_admin(client, test_app):
    """Test that a non-admin user cannot register a new manager."""
    with test_app.test_request_context():
        session["user"] = {"role": "manager"}

        query = """
        mutation {
          registerManager(name: "Unauthorized", password: "password", branch: "Test Branch") {
            manager {
              name
            }
          }
        }
        """

        response = client.execute(query)

        assert response is not None
        assert "errors" in response
        assert "Access requires role: admin" in response["errors"][0]["message"]


def test_delete_manager_as_admin(client, test_app, sample_admin, sample_manager):
    """Test that an admin can delete a manager."""
    with test_app.test_request_context():
        session["user"] = {"role": "admin"}

        query = """
        mutation {
          deleteManager(id: "1") {
            success
            message
          }
        }
        """

        response = client.execute(query)
        data = response.get("data", {}).get("deleteManager", {})

        assert response is not None
        assert "errors" not in response
        assert data["success"] is True
        assert "deleted successfully" in data["message"]


def test_delete_manager_as_non_admin(client, test_app, sample_manager):
    """Test that a non-admin user cannot delete a manager."""
    with test_app.test_request_context():
        session["user"] = {"role": "manager"}

        query = """
        mutation {
          deleteManager(id: "1") {
            success
            message
          }
        }
        """

        response = client.execute(query)

        assert response is not None
        assert "errors" in response
        assert "Access requires role: admin" in response["errors"][0]["message"]
