from flask import Flask, Blueprint
from flask_restx import Api
from flask_cors import CORS
from dotenv import load_dotenv
from db import init_db
import os
from user_service import users
from deeper_service import deepers

def get_v1() -> Blueprint:
    blueprint = Blueprint('api', __name__, url_prefix='/api')
    api = Api(blueprint, version='1.0', title='DEE:P API', description='DEE:P API DOCUMENT')
    api.add_namespace(users, path="/users")
    api.add_namespace(deepers, path="/deepers")
    return blueprint

app = Flask(__name__)
app.register_blueprint(get_v1())
CORS(app)

if __name__ == "__main__":
    load_dotenv()
    init_db()
    app.run(host=os.getenv('IP'), port=os.getenv('PORT'), debug=True)
