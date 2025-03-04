from graphene import ObjectType
from .application import ApplicationQuery
from .all_applications import AllApplicationQuery


class Query(ApplicationQuery, AllApplicationQuery, ObjectType):
    pass
