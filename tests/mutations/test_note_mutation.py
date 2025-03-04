import pytest
import uuid

from datetime import datetime
from graphene.test import Client

from app.api.graphql.schema import schema
from app.models import db, Application, ApplicationHistory
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
    """Creates a sample application in the test database with notes."""
    application = Application(
        id=7,
        client_name="Иванов Иван",
        phone_number="79123456701",
        branch_id=1,
        product="Test Product",
        status="in-progress",
        notes=[
            {"id": "7273dfd0-4436-4703-ad7e-fdaa21507299", "text": "Original note", "timestamp": "2025-01-01T10:05:00"},
        ],
        created_at=datetime.utcnow(),
    )

    db.session.add(application)
    db.session.commit()
    return application


def test_add_note_to_application(client, sample_application):
    """Test adding a note to an application."""
    mutation = """
    mutation {
      addNoteToApplication(id: "7", note: {text: "New note!"}) {
        application {
          id
          clientName
          notes {
            text
            timestamp
          }
        }
      }
    }
    """

    response = client.execute(mutation)
    data = response.get("data", {}).get("addNoteToApplication", {}).get("application", {})

    assert response is not None
    assert "errors" not in response
    assert data["id"] == "7"
    assert len(data["notes"]) == 2  # There should be 2 notes now
    assert any(note["text"] == "New note!" for note in data["notes"])


def test_update_note_from_application(client, sample_application):
    """Test updating an existing note."""
    mutation = """
    mutation {
      updateNoteFromApplication(id: "7", noteId: "7273dfd0-4436-4703-ad7e-fdaa21507299", newNote: {text: "Updated note!"}) {
        application {
          id
          clientName
          notes {
            text
          }
        }
      }
    }
    """

    response = client.execute(mutation)
    data = response.get("data", {}).get("updateNoteFromApplication", {}).get("application", {})

    assert response is not None
    assert "errors" not in response
    assert data["id"] == "7"
    assert any(note["text"] == "Updated note!" for note in data["notes"])


def test_remove_note_from_application(client, sample_application):
    """Test removing a note from an application."""
    mutation = """
    mutation {
      removeNoteFromApplication(id: "7", noteId: "7273dfd0-4436-4703-ad7e-fdaa21507299") {
        application {
          id
          notes {
            id
            text
          }
        }
      }
    }
    """

    response = client.execute(mutation)
    data = response.get("data", {}).get("removeNoteFromApplication", {}).get("application", {})

    assert response is not None
    assert "errors" not in response
    assert data["id"] == "7"
    assert len(data["notes"]) == 0  # Note should be removed
