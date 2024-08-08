from flask import Blueprint, jsonify


api_bp = Blueprint('api', __name__)


# Define a route for the root URL
@api_bp.route('/')
def index():
    return 'Welcome to the main page. Go to /dash for the Dash app or /api/data for the API.'

@api_bp.route("/api/data")
def get_data():
    return jsonify({"data": [1, 2, 3, 4, 5]})