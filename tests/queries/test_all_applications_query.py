import pytest
import random

from datetime import datetime
from graphene.test import Client

from app.api.graphql.schema import schema
from app.models import db, Application, ApplicationHistory, Branch
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


def sample_application(test_app):
    """Creates a sample application in the test database."""
    with test_app.app_context():
        # Ensure a branch exists before creating an application
        branch = Branch.query.filter_by(id=1).first()
        if not branch:
            branch = Branch(id=1, name="Test Branch")
            db.session.add(branch)
            db.session.commit()

        app_id = random.randint(1000, 9999)
        application = Application(
            id=app_id,
            client_name="Иванов Иван",
            phone_number="79123456701",
            branch_id=1,
            product="Test Product",
            status="closed",
            notes=[
                {"id": "af44d2dc-a633-401f-b2b0-4761fee5e68b", "isUpdated": False, "timestamp": "2025-01-01T10:05:00"},
                {"id": "4d41f57a-ce28-46bc-b97d-03c2276567a5", "isUpdated": False, "timestamp": "2025-03-02T14:00:00"},
                {"id": "dfe138a4-2459-493b-87ca-909f3dd330af", "isUpdated": False, "timestamp": "2025-03-02T14:00:00"},
                {"id": "31d0f9ca-e5ae-4881-97cb-f3473120e301", "isUpdated": False,
                 "timestamp": "2025-03-03T19:13:00.927156"},
            ],
            created_at=datetime.utcnow(),
        )

        history_entry = ApplicationHistory(
            id=random.randint(100, 999),
            application_id=app_id,
            changed_at="2025-03-03T18:22:07.804167",
            new_values="{'status': 'closed'}",
            updated_fields=["status"],
            previous_values="{'status': 'in-progress'}"
        )

        db.session.add(application)
        db.session.add(history_entry)
        db.session.commit()

        return application


def test_fetch_all_applications(client, sample_applications):
    """Test GraphQL query for fetching all applications."""
    query = """
    query {
      fetchAllApplication(first: 10) {
        applications {
          id
          clientName
          phoneNumber
          status
          branchId
        }
        totalCount
        totalClosedCount
        totalTransferredCount
        totalInProgressCount
      }
    }
    """

    response = client.execute(query)
    data = response.get("data", {}).get("fetchAllApplication", {})

    assert response is not None
    assert "errors" not in response
    assert len(data["applications"]) == 3  # We inserted 3 applications
    assert data["totalCount"] == 3
    assert data["totalClosedCount"] == 1
    assert data["totalTransferredCount"] == 1
    assert data["totalInProgressCount"] == 1

    # Check individual applications
    expected_clients = {"Иванов Иван", "Петров Петр", "Сидоров Алексей"}
    actual_clients = {app["clientName"] for app in data["applications"]}

    assert expected_clients == actual_clients
