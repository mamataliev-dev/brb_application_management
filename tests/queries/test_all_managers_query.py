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
def sample_managers(test_app):
    """Creates sample managers in the test database."""
    with test_app.app_context():
        branch = Branch.query.filter_by(name="Test Branch").first()
        if not branch:
            branch = Branch(name="Test Branch")
            db.session.add(branch)
            db.session.commit()

        managers = [
            Manager(id=1, name="John Doe", branch_name="Test Branch", created_at="2025-01-02T09:00:00", role="manager"),
            Manager(id=2, name="Jane Smith", branch_name="Test Branch", created_at="2025-02-10T10:30:00", role="manager"),
        ]

        db.session.bulk_save_objects(managers)
        db.session.commit()

        return managers

def test_fetch_all_managers_as_admin(client, test_app, sample_managers):
    """Test that an admin can fetch all managers."""
    with test_app.test_request_context():
        with test_app.test_client() as test_client:
            with test_client.session_transaction() as test_session:
                test_session["user"] = {"role": "admin"}

            query = """
            query {
              fetchAllManagers(limit: 10) {
                id
                name
                branch
                createdAt
              }
            }
            """

            response = client.execute(query)
            data = response.get("data", {}).get("fetchAllManagers", [])

            assert response is not None
            assert "errors" not in response
            assert len(data) == 2
            assert data[0]["name"] == "John Doe"
            assert data[1]["name"] == "Jane Smith"

def test_fetch_all_managers_as_manager(client, test_app, sample_managers):
    """Test that a manager cannot fetch all managers."""
    with test_app.test_request_context():
        session["user"] = {"role": "manager"}

        query = """
        query {
          fetchAllManagers(limit: 10) {
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

def test_fetch_all_managers_unauthenticated(client, test_app, sample_managers):
    """Test that an unauthenticated user cannot fetch all managers."""
    with test_app.test_request_context():
        session.clear()

        query = """
        query {
          fetchAllManagers(limit: 10) {
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