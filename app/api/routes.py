from app.api.resources import *


def register_api_resources(api):
    """Register all RESTful resources"""
    api.add_resource(RequestResource, '/requests/<int:request_id>')
    api.add_resource(RequestListResource, '/requests')

    api.add_resource(RequestHistoryListResource, '/requests-history')
    api.add_resource(RequestHistoryResource, '/requests-history/<int:request_id>')
