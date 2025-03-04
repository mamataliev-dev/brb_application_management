import pytest

from datetime import datetime
from graphene.test import Client

from app.api.graphql.schema import schema
from app.models import db, Application
from app import create_app


@pytest.fixture
def test_app():
    """Fixture to create a test app instance."""
    app = create_app(testing=True)
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
def sample_application(test_app):
    """Creates a sample application in the test database."""
    application = Application(
        id=1,
        client_name="Иванов Иван",
        phone_number="79123456701",
        branch_id=1,
        product="Test Product",
        status="in-progress",
        created_at=datetime.utcnow(),
        is_deleted=False
    )

    db.session.add(application)
    db.session.commit()
    return application


def test_update_application(client, sample_application):
    """Test updating an application's status."""
    mutation = """
    mutation {
      updateApplication(input: {
        id: "1"
        status: "closed"
      }) {
        application {
          id
          clientName
          status
        }
      }
    }
    """

    response = client.execute(mutation)
    data = response.get("data", {}).get("updateApplication", {}).get("application", {})

    assert response is not None
    assert "errors" not in response
    assert data["id"] == "1"
    assert data["clientName"] == "Иванов Иван"
    assert data["status"] == "closed"  # The status should now be updated


def test_delete_application(client, sample_application):
    """Test soft-deleting an application."""
    mutation = """
    mutation {
      deleteApplication(id: "1") {
        success
        message
      }
    }
    """

    response = client.execute(mutation)
    data = response.get("data", {}).get("deleteApplication", {})

    assert response is not None
    assert "errors" not in response
    assert data["success"] is True
    assert "Application 1 soft-deleted" in data["message"]

    # Ensure application is marked as deleted in the database
    application = Application.query.get(1)
    assert application.is_deleted is True
    assert application.deleted_at is not None
