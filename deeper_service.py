from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
from db import cursor, conn
from marshmallow import ValidationError
from schema import DeeperSchema
import http.client

deepers = Namespace('deepers', description='deepers')

deeper_schema = DeeperSchema()

create_deeper_request_model = deepers.model('CreateDeeperRequest', {
    'user_id': fields.String(required=True),
    'name': fields.String(required=True),
    'phone': fields.String(required=True),
    'extra_info': fields.String(),
    'memo': fields.String()
})

update_deeper_request_model = deepers.model('UpdateDeeperRequest', {
    'name': fields.String(required=True),
    'phone': fields.String(required=True),
    'extra_info': fields.String(),
    'memo': fields.String()
})

deepers_model = deepers.model('Deepers', {
    'id': fields.Integer(),
    'user_id': fields.String(),
    'name': fields.String(),
    'phone': fields.String(),
    'extra_info': fields.String(),
    'memo': fields.String()
})

@deepers.route("")
class Deeper(Resource):
    @deepers.expect(create_deeper_request_model)
    @deepers.response(code=201, description=http.client.responses.get(201))
    def post(self):
        try:
            data = deeper_schema.load(request.json)
        except ValidationError as err:
            return jsonify({"message": err.messages}), 400

        user = cursor.execute("SELECT * FROM users WHERE id = ?", (data["user_id"],)).fetchone()
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        cursor.execute("INSERT INTO deepers (user_id, name, phone, extra_info, memo) VALUES (?, ?, ?, ?, ?)",
                    (data["user_id"], data["name"], data["phone"], data.get("extra_info", ""), data.get("memo", "")))
        conn.commit()
        # deeper_id = cursor.lastrowid
        return None, 201
    
    @deepers.marshal_list_with(deepers_model)
    @deepers.response(code=200, description=http.client.responses.get(200))
    def get(self):
        user_id = request.args.get("user_id")
        if user_id:
            deepers = cursor.execute("SELECT * FROM deepers WHERE user_id = ?", (user_id,)).fetchall()
        else:
            deepers = cursor.execute("SELECT * FROM deepers").fetchall()
        return [dict(deeper) for deeper in deepers], 200

@deepers.route("/<id>")
class DeeperByID(Resource):
    @deepers.marshal_with(deepers_model)
    @deepers.response(code=200, description=http.client.responses.get(200))
    def get(self, id):
        deeper = cursor.execute("SELECT * FROM deepers WHERE id = ?", (id,)).fetchone()
        if not deeper:
            return jsonify({"message": "Deeper not found"}), 404
        return dict(deeper), 200
    
    @deepers.expect(update_deeper_request_model)
    @deepers.response(code=200, description=http.client.responses.get(200))
    def put(self, id):
        deepers = cursor.execute("SELECT * FROM deepers WHERE id = ?", (id,)).fetchone()
        if not deepers:
            return jsonify({"message": "Deeper not found"}), 404
        
        try:
            data = deeper_schema.load(request.json, partial=True)
        except ValidationError as err:
            return jsonify({"message": err.messages}), 400

        cursor.execute("UPDATE deepers SET name = ?, phone = ?, extra_info = ?, memo = ? WHERE id = ?",
            (data["name"], data["phone"], data.get("extra_info", ""), data.get("memo", ""), id))
        conn.commit()

        return None, 200
    
    @deepers.response(code=204, description=http.client.responses.get(204))
    def delete(self, id):
        deepers = cursor.execute("SELECT * FROM deepers WHERE id = ?", (id,)).fetchone()
        if not deepers:
            return jsonify({"message": "Deeper not found"}), 404

        cursor.execute("DELETE FROM deepers WHERE id = ?", (id,))
        conn.commit()

        return None, 204