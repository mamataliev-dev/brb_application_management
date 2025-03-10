from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Index, Boolean
from sqlalchemy.orm import relationship

from app.extensions import db


class Admin(db.Model):
    __tablename__ = 'admin'

    id = Column(Integer, primary_key=True)
    password = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False, default='admin')


class ApplicationHistory(db.Model):
    """
    Tracks changes to an application.

    Attributes:
        id (int): Primary key for the history record.
        application_id (int): Foreign key referencing the application being modified.
        changed_at (datetime): Timestamp when the change was made.
        updated_fields (JSON): List of fields that were changed.
        previous_values (JSON): Stores the previous values before the update.
        new_values (JSON): Stores the new values after the update.

    Relationships:
        application (Application): The application this history entry is associated with.
    """
    __tablename__ = "application_history"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"),
                            nullable=False)
    updated_fields = Column(JSON, nullable=False)
    previous_values = Column(JSON, nullable=False)
    new_values = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_by = Column(String(255))

    application = relationship("Application", back_populates="history")


class Branch(db.Model):
    """
    Represents a branch in the system.

    A branch is a physical or logical location that can have multiple managers
    and handle multiple client applications. Each branch has a unique name and
    maintains a record of when it was created.

    Attributes:
        id (int): Primary key for the branch.
        name (str): Unique name of the branch (max 100 characters).
        created_at (datetime): Timestamp when the branch was created.

    Relationships:
        managers (List[Manager]): List of managers associated with this branch.
        applications (List[Application]): List of applications handled by this branch.
    """
    __tablename__ = 'branches'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    managers = relationship("Manager", back_populates="branch")
    applications = relationship("Application", back_populates="branch")

    __table_args__ = (
        Index("idx_branch_name", "name"),
    )


class Manager(db.Model):
    """
    Represents a manager in the system.

    A manager is associated with a specific branch and can handle applications
    for that branch. Each manager has a name and a record of when they were added.

    Attributes:
        id (int): Primary key for the manager.
        username (str): Unique username of the manager for login.
        name (str): Name of the manager (max 100 characters).
        branch (int): Foreign key referencing the branch the manager belongs to.
        created_at (datetime): Timestamp when the manager was added.

    Relationships:
        branch (Branch): The branch this manager is associated with.
    """
    __tablename__ = 'managers'

    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    branch_name = Column(String(100), ForeignKey('branches.name'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    role = Column(String(255), nullable=False, default='manager')

    branch = relationship("Branch", back_populates="managers")

    __table_args__ = (
        Index("idx_manager_name", "name"),
        Index("idx_manager_username", "username")
    )


class Application(db.Model):
    """
    Represents an application in the system.

    An application is associated with a specific branch and contains details about
    the client, the product they are inquiring about, and the status of the application.
    The application also maintains a history of changes and optional notes.

    Attributes:
        id (int): Primary key for the application.
        client_name (str): Name of the client (max 255 characters).
        phone_number (str): Contact number of the client (max 20 characters).
        request_datetime (datetime): Timestamp when the application was created.
        branch_id (int): Foreign key referencing the branch handling the application.
        product (str): Name of the product the client is inquiring about (max 255 characters).
        status (str): Current status of the application. Possible values:
            - 'in-progress'
            - 'closed'
            - 'transferred'
        notes (JSON): Optional notes about the application.

    Relationships:
        branch (Branch): The branch handling this application.
        history_entries (List[ApplicationHistory]): History of changes made to the application.
    """
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True)
    client_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    branch_name = Column(String(100), ForeignKey('branches.name'), nullable=False)
    product = Column(String(255), nullable=False)
    status = Column(String(100), nullable=False, default='in-progress')
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    deleted_by = Column(String(255))
    notes = Column(JSON, default=[])

    history = relationship("ApplicationHistory", back_populates="application", cascade="all, delete-orphan")
    branch = relationship("Branch", back_populates="applications")

    __table_args__ = (
        Index("idx_phone_number", "phone_number"),
        Index("idx_is_deleted", "is_deleted"),
    )
