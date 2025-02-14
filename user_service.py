from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
from db import cursor, conn
from marshmallow import ValidationError
from schema import UserSchema
import http.client
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import os

users = Namespace('users', description='users')

user_schema = UserSchema()

create_user_request_model = users.model('CreateUserRequest', {
    'id': fields.String(required=True),
    'name': fields.String(required=True),
    'phone': fields.String(required=True),
    'extra_info': fields.String(),
})

update_user_request_model = users.model('UpdateUserRequest', {
    'name': fields.String(required=True),
    'phone': fields.String(required=True),
    'extra_info': fields.String(),
})

users_model = users.model('Users', {
    'id': fields.String(),
    'name': fields.String(),
    'phone': fields.String(),
    'extra_info': fields.String(),
    'deepers': fields.List(fields.Raw()),
})

@users.route("")
class User(Resource):
    @users.expect(create_user_request_model)
    @users.response(code=201, description=http.client.responses.get(201))
    def post(self):
        try:
            data = user_schema.load(request.json)
        except ValidationError as err:
            return jsonify({"message": err.messages}), 400

        cursor.execute("INSERT INTO users (id, name, phone, extra_info) VALUES (?, ?, ?, ?)",
                    (data["id"], data["name"], data["phone"], data.get("extra_info", "")))
        conn.commit()
        # user_id = cursor.lastrowid
        return None, 201
    
    @users.marshal_list_with(users_model)
    @users.response(code=200, description=http.client.responses.get(200))
    def get(self):
        users = cursor.execute("SELECT * FROM users").fetchall()
        return [dict(user) for user in users], 200

@users.route("/<id>")
class UserByID(Resource):
    @users.marshal_with(users_model)
    @users.response(code=200, description=http.client.responses.get(200))
    def get(self, id):
        user = cursor.execute("SELECT * FROM users WHERE id = ?", (id,)).fetchone()
        if not user:
            return jsonify({"message": "User not found"}), 404
        user_data = dict(user)
        deepers = cursor.execute("SELECT * FROM deepers WHERE user_id = ?", (id,)).fetchall()
        user_data["deepers"] = [dict(deeper) for deeper in deepers]
        return user_data, 200
    
    @users.expect(update_user_request_model)
    @users.response(code=200, description=http.client.responses.get(200))
    def put(self, id):
        user = cursor.execute("SELECT * FROM users WHERE id = ?", (id,)).fetchone()
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        try:
            data = user_schema.load(request.json, partial=True)
        except ValidationError as err:
            return jsonify({"message": err.messages}), 400

        cursor.execute("UPDATE users SET name = ?, phone = ?, extra_info = ? WHERE id = ?",
            (data["name"], data["phone"], data.get("extra_info", ""), id))
        conn.commit()

        return None, 200
    
    @users.response(code=204, description=http.client.responses.get(204))
    def delete(self, id):
        user = cursor.execute("SELECT * FROM users WHERE id = ?", (id,)).fetchone()
        if not user:
            return jsonify({"message": "User not found"}), 404

        cursor.execute("DELETE FROM users WHERE id = ?", (id,))
        conn.commit()

        return None, 204

@users.route("/<id>/encrypted")
class UserEncrypted(Resource):
    @users.response(code=200, description=http.client.responses.get(200))
    def get(self, id):
        user = cursor.execute("SELECT * FROM users WHERE id = ?", (id,)).fetchone()
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        # 16바이트 크기의 랜덤 IV 생성
        iv = get_random_bytes(16)
        
        # 데이터를 128비트 블록 크기에 맞게 패딩
        padded_data = pad(id.encode(), AES.block_size)
        
        # SECRET_KEY를 바이트 형식으로 변환 (AES.new에서 바이트 형식 필요)
        secret_key = os.getenv('SECRET_KEY').encode('utf-8')

        # AES 암호화 객체 생성 (CBC 모드 사용)
        cipher = AES.new(secret_key, AES.MODE_CBC, iv)

        # 암호화 실행
        ciphertext = cipher.encrypt(padded_data)

        # 암호문 앞에 IV를 추가하여 반환 (복호화 시 필요)
        res = iv + ciphertext

        return res.hex(), 200
    
@users.route("/security/<id>")
class UserSecurity(Resource):
    @users.response(code=200, description=http.client.responses.get(200))
    def get(self, id):
        ciphertext = bytes.fromhex(id)
        
        # 암호문에서 IV 추출
        iv = ciphertext[:16]
        ciphertext = ciphertext[16:]

        # SECRET_KEY를 바이트 형식으로 변환 (AES.new에서 바이트 형식 필요)
        secret_key = os.getenv('SECRET_KEY').encode('utf-8')
        
        # AES 암호화 객체 생성 (CBC 모드 사용)
        cipher = AES.new(secret_key, AES.MODE_CBC, iv)

        # 복호화 실행
        decrypted_padded_data = cipher.decrypt(ciphertext)

        # 패딩 제거
        plaintext = unpad(decrypted_padded_data, AES.block_size)

        user_id = plaintext.decode()

        user = cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return jsonify({"message": "User not found"}), 404

        return dict(user), 200