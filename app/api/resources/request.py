from datetime import datetime
from flask_restful import Resource
from flask import request
from sqlalchemy.orm.attributes import flag_modified
from flask_cors import cross_origin

from app.models import Branch, Manager, Request, RequestTransfer, RequestHistory
from app.extensions import db


class RequestResource(Resource):
    @cross_origin()
    def get(self, request_id):
        user_request = self._fetch_request_by_id(request_id)

        if not user_request:
            return {'error': 'Request not found'}, 404

        return self._build_request_response(user_request), 200

    @cross_origin()
    def put(self, request_id):
        data = request.get_json()
        user_request = self._fetch_request_by_id(request_id)

        if not user_request:
            return {"error": "Request not found"}, 404

        previous_values = self._get_current_values(user_request)
        updated_fields, new_values = self._update_request(user_request, data)

        if "notes" in data and data["notes"]:
            updated_notes = self._append_json_note(user_request.notes, data["notes"])
            user_request.notes = updated_notes
            flag_modified(user_request, "notes")
            updated_fields.append("notes")
            new_values["notes"] = updated_notes

        db.session.commit()

        if updated_fields:
            self._log_request_history(user_request.id, updated_fields, previous_values, new_values)

        return self._build_request_response(user_request), 200

    @cross_origin()
    def delete(self, request_id):
        user_request = self._fetch_request_by_id(request_id)

        if not user_request:
            return {"error": "Request not found"}, 404

        db.session.delete(user_request)
        db.session.commit()

        return {"message": "Request deleted"}, 200

    def _log_request_history(self, request_id, updated_fields, previous_values, new_values):
        history_entry = RequestHistory(
            request_id=request_id,
            updated_fields=updated_fields,
            previous_values=previous_values,
            new_values=new_values
        )
        db.session.add(history_entry)
        db.session.commit()

    def _get_current_values(self, request):
        return {
            "client_name": request.client_name,
            "phone_number": request.phone_number,
            "branch_id": request.branch_id,
            "product": request.product,
            "status": request.status,
            "notes": request.notes
        }

    def _update_request(self, request, new_data):
        updated_fields = []
        new_values = {}

        for field in ["client_name", "phone_number", "branch_id", "product", "status"]:
            new_value = new_data.get(field)
            if new_value is not None and getattr(request, field) != new_value:
                updated_fields.append(field)
                new_values[field] = new_value
                setattr(request, field, new_value)

        return updated_fields, new_values

    def _append_json_note(self, existing_notes, new_note):
        note_entry = {"timestamp": datetime.utcnow().isoformat(), "text": new_note}

        if not existing_notes or not isinstance(existing_notes, list):
            existing_notes = []

        existing_notes.append(note_entry)
        return existing_notes

    def _get_field_or_default(self, new_value, current_value):
        return new_value if new_value is not None else current_value

    def _fetch_request_by_id(self, request_id):
        return Request.query.filter(Request.id == request_id).first()

    def _build_request_response(self, data):
        return {
            "id": data.id,
            "client_name": data.client_name,
            "phone_number": data.phone_number,
            "request_datetime": data.request_datetime.isoformat(),
            "branch_id": data.branch_id,
            "product": data.product,
            "status": data.status,
            "notes": data.notes if isinstance(data.notes, list) else []
        }


class RequestListResource(Resource):
    def __init__(self):
        self.request_resource = RequestResource()

    @cross_origin()
    def get(self):
        branch_id = request.args.get("branch_id", type=int)
        status = request.args.get("status", type=str)
        start_date = request.args.get("start_date", type=str)  # Format: YYYY-MM-DD
        end_date = request.args.get("end_date", type=str)  # Format: YYYY-MM-DD
        product = request.args.get("product", type=str)

        client_name = request.args.get("client_name", type=str)
        phone_number = request.args.get("phone_number", type=str)

        query = Request.query

        if branch_id:
            query = query.filter(Request.branch_id == branch_id)
        if status:
            query = query.filter(Request.status == status)
        if start_date and end_date:
            query = query.filter(Request.request_datetime.between(start_date, end_date))
        elif start_date:
            query = query.filter(Request.request_datetime >= start_date)
        elif end_date:
            query = query.filter(Request.request_datetime <= end_date)

        if client_name and phone_number:
            query = query.filter(
                (Request.client_name.ilike(f"%{client_name}%")) | (Request.phone_number.ilike(f"%{phone_number}%")))
        elif client_name:
            query = query.filter(Request.client_name.ilike(f"%{client_name}%"))
        elif phone_number:
            query = query.filter(Request.phone_number.ilike(f"%{phone_number}%"))

        results = query.all()
        return {
            "requests":
                [self.request_resource._build_request_response(req) for req in results]
        }, 200


class RequestHistoryResource(Resource):
    @cross_origin()
    def get(self, request_id):
        history_entries = self._fetch_request_history_by_id(request_id)

        return {
            "history":
                [self._build_request_history_response(history) for history in history_entries]
        }, 200

    def _fetch_request_history_by_id(self, request_id):
        return RequestHistory.query.filter_by(request_id=request_id).order_by(
            RequestHistory.changed_at.desc()).all()

    def _build_request_history_response(self, history):
        return {
            "id": history.id,
            "request_id": history.request_id,
            "changed_at": history.changed_at.isoformat(),
            "updated_fields": history.updated_fields,
            "previous_values": history.previous_values,
            "new_values": history.new_values
        }


class RequestHistoryListResource(Resource):
    @cross_origin()
    def get(self):
        history_entries = RequestHistory.query.all()

        return {
            "requests":
                [self._build_request_history_response(history) for history in history_entries]
        }, 200

    def _build_request_history_response(self, history):
        return {
            "id": history.id,
            "request_id": history.request_id,
            "changed_at": history.changed_at.isoformat(),
            "updated_fields": history.updated_fields,
            "previous_values": history.previous_values,
            "new_values": history.new_values
        }
