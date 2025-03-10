from graphene import ObjectType
from .application import ApplicationQuery
from .all_applications import AllApplicationQuery
from .all_mamagers import AllManagersQuery
from .manager import ManagerQuery


class Query(ApplicationQuery, AllApplicationQuery, AllManagersQuery, ManagerQuery, ObjectType):
    pass
