from graphene import ObjectType

from .application import UpdateApplication, DeleteApplication
from .note import AddNoteToApplication, RemoveNoteFromApplication, UpdateNoteFromApplication
from app.api.graphql.mutations.auth.auth_admin import LoginAdmin
from app.api.graphql.mutations.auth.auth_manager import RegisterManager, LoginManager, LogoutManager, DeleteManager
from app.api.graphql.mutations.manager import UpdateManager


class ApplicationMutations(ObjectType):
    update_application = UpdateApplication.Field()
    delete_application = DeleteApplication.Field()

    update_manager = UpdateManager.Field()

    add_note_to_application = AddNoteToApplication.Field()
    remove_note_from_application = RemoveNoteFromApplication.Field()
    update_note_from_application = UpdateNoteFromApplication.Field()

    login_admin = LoginAdmin.Field()

    register_manager = RegisterManager.Field()
    login_manager = LoginManager.Field()
    logout_manager = LogoutManager.Field()
    delete_manager = DeleteManager.Field()
