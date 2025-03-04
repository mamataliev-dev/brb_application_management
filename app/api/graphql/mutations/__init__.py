from graphene import ObjectType

from .application import UpdateApplication, DeleteApplication, AddNoteToApplication
from .note import AddNoteToApplication, RemoveNoteFromApplication, UpdateNoteFromApplication


class ApplicationMutations(ObjectType):
    update_application = UpdateApplication.Field()
    delete_application = DeleteApplication.Field()
    add_note_to_application = AddNoteToApplication.Field()
    remove_note_from_application = RemoveNoteFromApplication.Field()
    update_note_from_application = UpdateNoteFromApplication.Field()
