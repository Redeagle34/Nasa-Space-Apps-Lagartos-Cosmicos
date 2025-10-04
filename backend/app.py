from flask import Flask, jsonify
from flask_cors import CORS

# Create the Flask app instance
app = Flask(__name__)

# Enable CORS to allow requests from the React frontend
CORS(app)

# Define a simple API endpoint
@app.route("/api/message", methods=['GET'])
def get_message():
    """Returns a simple JSON message."""
    return jsonify(message="TESTEST! 👋")

if __name__ == '__main__':
    # Run the app on port 3000, accessible from any IP
    app.run(host='0.0.0.0', port=5000)