from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Enum, Index
from sqlalchemy.orm import relationship

from app.extensions import db


class RequestHistory(db.Model):
    """
    Tracks changes to requests.

    Attributes:
        id (int): Primary key for the history record.
        request_id (int): Foreign key referencing the request being modified.
        changed_at (datetime): Timestamp when the change was made.
        updated_fields (JSON): List of fields that were changed.
        previous_values (JSON): Stores the previous values before the update.
        new_values (JSON): Stores the new values after the update.

    Relationships:
        request (Request): The request this history entry is associated with.
    """
    __tablename__ = "request_history"

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_fields = Column(JSON, nullable=False)
    previous_values = Column(JSON, nullable=False)
    new_values = Column(JSON, nullable=False)

    request = relationship("Request", back_populates="history_entries")


class Branch(db.Model):
    """
    Represents a branch in the system.

    A branch is a physical or logical location that can have multiple managers
    and handle multiple client requests. Each branch has a unique name and
    maintains a record of when it was created.

    Attributes:
        id (int): Primary key for the branch.
        name (str): Unique name of the branch (max 100 characters).
        created_at (datetime): Timestamp when the branch was created.

    Relationships:
        managers (List[Manager]): List of managers associated with this branch.
        requests (List[Request]): List of requests handled by this branch.
    """
    __tablename__ = 'branches'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)

    managers = relationship("Manager", back_populates="branch")
    requests = relationship("Request", back_populates="branch")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_branch_name", "name")
    )


class Manager(db.Model):
    """
    Represents a manager in the system.

    A manager is associated with a specific branch and can handle requests
    for that branch. Each manager has a name and a record of when they were added.

    Attributes:
        id (int): Primary key for the manager.
        name (str): Name of the manager (max 100 characters).
        branch_id (int): Foreign key referencing the branch the manager belongs to.
        created_at (datetime): Timestamp when the manager was added.

    Relationships:
        branch (Branch): The branch this manager is associated with.
    """
    __tablename__ = 'managers'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch", back_populates="managers")


class Request(db.Model):
    """
    Represents a client request in the system.

    A request is associated with a specific branch and contains details about
    the client, the product they are inquiring about, and the status of the request.
    The request also maintains a history of changes and optional notes.

    Attributes:
        id (int): Primary key for the request.
        client_name (str): Name of the client (max 255 characters).
        phone_number (str): Contact number of the client (max 20 characters).
        request_datetime (datetime): Timestamp when the request was created.
        branch_id (int): Foreign key referencing the branch handling the request.
        product (str): Name of the product the client is inquiring about (max 255 characters).
        status (str): Current status of the request. Possible values:
            - 'In Progress'
            - 'Closed'
            - 'Transferred'
        notes (str): Optional notes about the request.
        history (JSON): History of changes made to the request.

    Relationships:
        branch (Branch): The branch handling this request.
    """
    __tablename__ = 'requests'

    id = Column(Integer, primary_key=True)
    client_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    request_datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    product = Column(String(255), nullable=False)
    status = Column(Enum('in-progress', 'closed', 'transferred', name="request_status"),
                    default='in-progress')
    notes = Column(JSON, default=[])
    history = Column(JSON, default=[])

    branch = relationship("Branch", back_populates="requests")
    history_entries = relationship("RequestHistory", back_populates="request", cascade="all, delete-orphan")
    created_at = Column(DateTime, default=0)

    __table_args__ = (
        Index("idx_client_name", "client_name"),
        Index("idx_phone_number", "phone_number"),
    )


class RequestTransfer(db.Model):
    """
    Represents the transfer of a request from one branch to another.

    When a request is transferred, this model records the request ID, the old branch,
    the new branch, and the timestamp of the transfer.

    Attributes:
        id (int): Primary key for the transfer record.
        request_id (int): Foreign key referencing the request being transferred.
        old_branch_id (int): Foreign key referencing the branch the request was transferred from.
        new_branch_id (int): Foreign key referencing the branch the request was transferred to.
        transferred_at (datetime): Timestamp when the transfer occurred.

    Relationships:
        request (Request): The request being transferred.
    """
    __tablename__ = 'request_transfers'

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('requests.id'), nullable=False)
    old_branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    new_branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    transferred_at = Column(DateTime, default=datetime.utcnow)

    request = relationship("Request", foreign_keys=[request_id])
