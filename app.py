import os
import urllib.parse
from datetime import datetime
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Initialize the Flask application
app = Flask(__name__)

# Fetch MongoDB configuration from environment variables
MONGO_USER = os.environ.get("MONGO_INITDB_ROOT_USERNAME") or os.environ.get("MONGO_USERNAME")
MONGO_PASS = os.environ.get("MONGO_INITDB_ROOT_PASSWORD") or os.environ.get("MONGO_PASSWORD")
MONGO_HOST = os.environ.get("MONGO_HOST", "localhost")
MONGO_PORT = os.environ.get("MONGO_PORT", "27017")
MONGO_DB = os.environ.get("MONGO_DB", "flask_db")
MONGO_AUTH_SOURCE = os.environ.get("MONGO_AUTH_SOURCE", "admin")

# Construct authenticated MongoDB URI if not provided directly
MONGODB_URI = os.environ.get("MONGODB_URI")
if not MONGODB_URI:
    if MONGO_USER and MONGO_PASS:
        user_enc = urllib.parse.quote_plus(MONGO_USER)
        pass_enc = urllib.parse.quote_plus(MONGO_PASS)
        MONGODB_URI = f"mongodb://{user_enc}:{pass_enc}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource={MONGO_AUTH_SOURCE}"
    else:
        MONGODB_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}"

# Set up the MongoDB client with a timeout for fast failure recovery
client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)

# Connect to the target database and collection
db = client[MONGO_DB]
collection = db.data


# Define the route for the root URL
@app.route('/')
def index():
    # Return a welcome message with the current time
    return f"Welcome to the Flask app! The current time is: {datetime.now()}"


# Define the route for the '/data' endpoint
# This endpoint supports both GET and POST methods
@app.route('/data', methods=['GET', 'POST'])
def data():
    try:
        if request.method == 'POST':
            # If the request method is POST, get the JSON data from the request
            data_payload = request.get_json()
            if not data_payload or not isinstance(data_payload, dict):
                return jsonify({"error": "Invalid or missing JSON payload"}), 400

            # Insert the data into the 'data' collection in MongoDB
            collection.insert_one(data_payload)

            # Return a success message with status code 201 (Created)
            return jsonify({"status": "Data inserted"}), 201

        elif request.method == 'GET':
            # If the request method is GET, retrieve all documents from the 'data' collection
            # Convert the documents to a list, excluding the '_id' field
            documents = list(collection.find({}, {"_id": 0}))

            # Return the data as a JSON response with status code 200 (OK)
            return jsonify(documents), 200

    except (ConnectionFailure, ServerSelectionTimeoutError) as err:
        return jsonify({
            "error": "Database connectivity failure",
            "message": str(err)
        }), 500
    except Exception as err:
        return jsonify({
            "error": "Internal server error",
            "message": str(err)
        }), 500


# Liveness and Readiness Probe Endpoint for Kubernetes
@app.route('/healthz', methods=['GET'])
def healthz():
    try:
        # Ping the MongoDB database to verify end-to-end connectivity
        client.admin.command('ping')
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as err:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(err)
        }), 503


# Run the Flask application
# The application will listen on all available IP addresses (0.0.0.0) and port 5000
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
