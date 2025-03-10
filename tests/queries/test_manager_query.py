import pytest
from graphene.test import Client
from flask import session
from app.api.graphql.schema import schema
from app.models import db, Manager, Branch
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
def sample_manager(test_app):
    """Creates a sample manager in the test database."""
    with test_app.app_context():
        branch = Branch.query.filter_by(name="Test Branch").first()
        if not branch:
            branch = Branch(name="Test Branch")
            db.session.add(branch)
            db.session.commit()

        manager = Manager(
            id=1,
            name="John Doe",
            branch_name="Test Branch",
            created_at="2025-01-02T09:00:00",
            role="manager"
        )

        db.session.add(manager)
        db.session.commit()

        return manager

def test_fetch_manager_by_id_as_admin(client, test_app, sample_manager):
    """Test that an admin can fetch a manager by ID."""
    with test_app.test_request_context():
        with test_app.test_client() as test_client:
            with test_client.session_transaction() as test_session:
                test_session["user"] = {"role": "admin"}

            query = """
            query {
              fetchManagerById(id: "1") {
                id
                name
                branch
                createdAt
              }
            }
            """

            response = client.execute(query)
            data = response.get("data", {}).get("fetchManagerById", {})

            assert response is not None
            assert "errors" not in response
            assert data["id"] == "1"
            assert data["name"] == "John Doe"
            assert data["branch"] == "Test Branch"
            assert data["createdAt"] == "2025-01-02T09:00:00"

def test_fetch_manager_by_id_as_manager(client, test_app, sample_manager):
    """Test that a manager cannot fetch another manager's details."""
    with test_app.test_request_context():
        session["user"] = {"role": "manager"}

        query = """
        query {
          fetchManagerById(id: "1") {
            id
            name
            branch
            createdAt
          }
        }
        """

        response = client.execute(query)

        assert response is not None
        assert "errors" in response
        assert "Access requires role: admin" in response["errors"][0]["message"]

def test_fetch_manager_by_id_unauthenticated(client, test_app, sample_manager):
    """Test that an unauthenticated user cannot fetch manager details."""
    with test_app.test_request_context():
        session.clear()

        query = """
        query {
          fetchManagerById(id: "1") {
            id
            name
            branch
            createdAt
          }
        }
        """

        response = client.execute(query)

        assert response is not None
        assert "errors" in response
        assert "Authentication required" in response["errors"][0]["message"]
