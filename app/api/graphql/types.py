from graphene import ObjectType, Enum, String, Int, ID, List, InputObjectType, DateTime, Boolean


class Note(ObjectType):
    id = String(required=True)
    text = String()
    timestamp = String()
    is_updated = Boolean(default_value=False)


class ApplicationHistory(ObjectType):
    id = ID()
    application_id = ID()
    changed_at = DateTime()
    updated_fields = List(String)
    previous_values = String()
    new_values = String()


class Application(ObjectType):
    id = ID()
    branch_id = Int()
    client_name = String()
    notes = List(Note)
    phone_number = String()
    product = String()
    created_at = String()
    status = String()
    history_entries = List(ApplicationHistory, description="History of changes to this application")
    is_deleted = Boolean()
    deleted_at = String()


class NoteInput(InputObjectType):
    text = String(required=True)


class UpdateApplicationInput(InputObjectType):
    id = ID(required=True)
    branch_id = ID()
    client_name = String()
    phone_number = String()
    product = String()
    status = String()
    notes = List(NoteInput)


class ApplicationSortField(Enum):
    ID = "id"
    CLIENT_NAME = "client_name"
    REQUEST_DATETIME = "request_datetime"


class SortDirection(Enum):
    ASC = "asc"
    DESC = "desc"


class ApplicationFilterInput(InputObjectType):
    branch_id = ID(description="Filter by branch ID")
    status = String(description="Filter by status (e.g., 'in-progress', 'closed')")


class ApplicationSortInput(InputObjectType):
    field = ApplicationSortField(required=True, description="Field to sort by")
    direction = SortDirection(default_value="ASC", description="Sort direction: ASC or DESC")


class BranchCount(ObjectType):
    branch_id = Int(description="ID of the branch")
    count = Int(description="Total number of applications for this branch")


class ApplicationConnection(ObjectType):
    applications = List(Application, description="List of applications")
    total_count = Int(description="Total number of applications")
    total_closed_count = Int(description="Total number of closed applications")
    total_transferred_count = Int(description="Total number of transferred applications")
    total_in_progress_count = Int(description="Total number of in-progress applications")
    branch_counts = List(BranchCount, description="Total counts of applications by branch ID")
