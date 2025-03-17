from graphene import ObjectType, Enum, String, Int, ID, List, InputObjectType, DateTime, Boolean


class Admin(ObjectType):
    password = String(required=True)
    role = String(default_value="admin")


class Manager(ObjectType):
    id = ID()
    username = String()
    name = String()
    password = String()
    branch = String()
    created_at = String()
    role = String(default_value="manager")


class Note(ObjectType):
    id = String(required=True)
    text = String()
    timestamp = String()
    is_updated = Boolean(default_value=False)
    updated_by = String()
    created_by = String()


class ApplicationHistory(ObjectType):
    id = ID()
    application_id = ID()
    updated_at = DateTime()
    updated_fields = List(String)
    previous_values = String()
    new_values = String()
    updated_by = String()


class Application(ObjectType):
    id = ID()
    branch = String()
    client_name = String()
    phone_number = String()
    product = String()
    created_at = String()
    status = String()
    is_deleted = Boolean()
    deleted_at = String()
    deleted_by = String()
    notes = List(Note)
    history = List(ApplicationHistory)


class NoteInput(InputObjectType):
    text = String(required=True)


class UpdateApplicationInput(InputObjectType):
    id = ID(required=True)
    branch_name = String()
    client_name = String()
    phone_number = String()
    product = String()
    status = String()
    notes = List(NoteInput)


class UpdateManagerInput(InputObjectType):
    id = ID(required=True)
    branch_name = String()
    name = String()
    password = String()


class ApplicationSortField(Enum):
    ID = "id"
    CLIENT_NAME = "client_name"
    APPLICATION_DATETIME = "application_datetime"


class SortDirection(Enum):
    ASC = "asc"
    DESC = "desc"


class ApplicationFilterInput(InputObjectType):
    branch = String(description="Filter by branch name")
    status = String(description="Filter by status (e.g., 'in-progress', 'closed')")


class ApplicationSortInput(InputObjectType):
    field = ApplicationSortField(required=True, description="Field to sort by")
    direction = SortDirection(default_value="ASC", description="Sort direction: ASC or DESC")


class BranchCount(ObjectType):
    branch = String(description="Name of the branch")
    count = Int(description="Total number of applications for this branch")


class ApplicationConnection(ObjectType):
    applications = List(Application, description="List of applications")
    total_count = Int(description="Total number of applications")
    total_closed_count = Int(description="Total number of closed applications")
    total_transferred_count = Int(description="Total number of transferred applications")
    total_in_progress_count = Int(description="Total number of in-progress applications")
    branch_counts = List(BranchCount, description="Total counts of applications by branch ID")
