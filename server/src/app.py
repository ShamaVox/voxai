from flask import Flask, Blueprint
from flask_cors import CORS

# Create a blueprint for API routes
# TODO: Port all APIs to this blueprint (currently only used for greenhouse)
api_bp = Blueprint('api', __name__, url_prefix='/api')

app = Flask(__name__, static_folder='../../client/dist')
CORS(app, resources={r"/*": {"origins": ["http://localhost:8081", "http://localhost:5000", "http://localhost:80", "http://localhost"]}})