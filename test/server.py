from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from flask import send_from_directory
import os

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Conexión a MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["sensor_db"]
collection = db["sensordata"]

@app.route("/")
def index():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'index.html')



@app.route("/data", methods=["POST"])
def receive_data():
    data = request.json
    data["timestamp"] = datetime.utcnow()
    collection.insert_one(data)
    socketio.emit("new_data", {
        "timestamp": data["timestamp"].strftime("%H:%M:%S"),
        "device": data["device"],
        "type": data["type"],
        "value": data["value"]
    })
    return jsonify({"status": "success"}), 200

@app.route("/data/latest", methods=["GET"])
def latest_data():
    last_data = list(collection.find().sort("timestamp", -1).limit(10))
    for d in last_data:
        d["_id"] = str(d["_id"])
        d["timestamp"] = d["timestamp"].strftime("%H:%M:%S")
    return jsonify(last_data)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=False)
