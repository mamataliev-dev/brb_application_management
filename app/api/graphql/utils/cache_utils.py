import json

from datetime import datetime

from app.extensions import redis_client
from app.api.graphql.utils.common_utils import NotesMapper
from app.api.graphql.types import Note, Application, Manager


def get_manager_from_cache(cache_key):
    cached_manager = redis_client.get(cache_key)

    if cached_manager:
        manager_dict = json.loads(cached_manager)

        manager_dict['created_at'] = (
            datetime.fromisoformat(manager_dict['created_at'])
            if manager_dict.get('created_at')
            else None
        )

        return Manager(**manager_dict)

    return None


def get_application_from_cache(cache_key):
    cached_application = redis_client.get(cache_key)

    if cached_application:
        application_dict = json.loads(cached_application)

        notes_data = application_dict.pop('notes', [])
        notes = [Note(**note_dict) for note_dict in notes_data] if notes_data else []

        application_dict['created_at'] = (
            datetime.fromisoformat(application_dict['created_at'])
            if application_dict.get('created_at')
            else None
        )
        application_dict['deleted_at'] = (
            datetime.fromisoformat(application_dict['deleted_at'])
            if application_dict.get('deleted_at')
            else None
        )

        history_data = application_dict.pop('history', [])
        history = [
            {
                **h,
                'updated_at': datetime.fromisoformat(h['updated_at']) if h.get('updated_at') else None
            }
            for h in history_data
        ]

        return Application(
            notes=notes,
            history=history,
            **application_dict
        )

    return None


def build_application_serialized_response(application):
    notes_mapper = NotesMapper()
    notes = notes_mapper.map_notes(application)

    return {
        "id": str(application.id),
        "branch": application.branch_name,
        "client_name": application.client_name,
        "phone_number": application.phone_number,
        "created_at": application.created_at.isoformat() if application.created_at else None,
        "product": application.product,
        "status": application.status,
        "deleted_at": application.deleted_at.isoformat() if application.deleted_at else None,
        "is_deleted": application.is_deleted,
        "deleted_by": application.deleted_by,
        "notes": _build_note_serialized_response(notes),
        "history": _build_history_serialized_response(application.history),
    }


def _build_history_serialized_response(history):
    return [
        {
            "id": h.id,
            "application_id": h.application_id,
            "updated_at": h.updated_at.isoformat() if h.updated_at else None,
            "updated_fields": h.updated_fields,
            "previous_values": h.previous_values,
            "new_values": h.new_values,
            "updated_by": h.updated_by,
        } for h in history
    ]


def _build_note_serialized_response(notes):
    return [
        {
            "id": note.id,
            "text": note.text,
            "timestamp": note.timestamp.isoformat() if isinstance(note.timestamp, datetime) else note.timestamp,
            "is_updated": note.is_updated,
            "created_by": note.created_by,
            "updated_by": note.updated_by
        } for note in notes
    ]


def cache_application_info(application, ttl=3600):
    redis_client.hset(
        f"application:{application.id}:info",
        mapping={
            "id": application.id,
            "branch": application.branch,
            "client_name": application.client_name,
            "phone_number": application.phone_number,
            "created_at": application.created_at,
            "product": application.product,
            "status": application.status,
            "deleted_at": application.deleted_at,
            "is_deleted": application.is_deleted,
            "deleted_by": application.deleted_by,
            "history": _build_history_serialized_response(application),
            "notes": _build_note_serialized_response(application.notes),
        }
    )
    redis_client.expire(f"application:{application.id}:info", ttl)


def deserialize_application_info(application_dict):
    application_dict['created_at'] = datetime.fromisoformat(application_dict['created_at'])
    return application_dict


def cache_application_history(application):
    return json.dumps([
        {
            "id": h.id,
            "application_id": h.application_id,
            "updated_at": h.updated_at.isoformat(),
            "updated_fields": h.updated_fields,
            "previous_values": h.previous_values,
            "new_values": h.new_values,
            "updated_by": h.updated_by
        } for h in application.history
    ])


def invalidate_application_cache(application_id):
    """Deletes application from redis"""
    redis_client.delete(f"application:{application_id}")
