from flask import Flask
from flask_cors import CORS

app = Flask(__name__, static_folder='../../client/dist')
CORS(app, resources={r"/*": {"origins": ["http://localhost:8081", "http://localhost:5000", "http://localhost:80"]}})