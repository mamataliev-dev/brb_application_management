from graphene import Schema
from .queries import Query
from .mutations import ApplicationMutations

schema = Schema(query=Query, mutation=ApplicationMutations)
