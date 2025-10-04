import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai
# import snowflake.connector  # Commented out for testing
# import joblib  # Commented out for testing

# --- INITIALIZATION ---
load_dotenv()
app = Flask(__name__)
# CORS is necessary to allow the React frontend to communicate with this backend
CORS(app)

# --- CONFIGURATIONS ---
# Configure Gemini Client
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-pro')

# Load the pre-trained Machine Learning model
# ml_model = joblib.load('weather_model.pkl')  # Commented out for testing

# --- HELPER FUNCTIONS ---

def parse_prompt_with_gemini(user_prompt):
    """Uses Gemini to extract structured data from a user's natural language prompt."""
    prompt_template = f"""
    You are an AI assistant for a weather app. Extract the 'location' from the user's request.
    Respond ONLY with a valid JSON object containing a "location" key.
    User request: "{user_prompt}"
    JSON output:
    """
    response = gemini_model.generate_content(prompt_template)
    return json.loads(response.text)

def get_mock_weather_data(location):
    """Returns mock weather data for testing purposes."""
    # Mock data structure that simulates what we'd get from Snowflake
    mock_data = {
        "San Pedro Garza Garcia": [
            (25.5, 65, 10),  # (temperature_c, humidity_percent, wind_speed_kph)
            (26.0, 68, 12),
            (24.5, 70, 8)
        ],
        "Monterrey": [
            (28.0, 55, 15),
            (27.5, 60, 14),
            (29.0, 58, 16)
        ]
    }
    return mock_data.get(location, [])

def get_mock_prediction(data):
    """Returns mock ML model predictions for testing purposes."""
    if not data:
        return None
    
    # Take the first data point and simulate a prediction
    temp, humidity, wind = data[0]
    return [
        [temp + 2, humidity + 5]  # Simulate a simple prediction by adding to current values
    ]

def format_prediction_with_gemini(prediction_data):
    """Uses Gemini to convert raw ML model output into a user-friendly format."""
    prompt_template = f"""
    You are a helpful weather assistant. Based on the following raw prediction data, generate a user-friendly response.
    The response must be a single, valid JSON object with two keys:
    1. "summary": A short, conversational paragraph.
    2. "table": A simple Markdown table with the key metrics.

    Prediction Data: {prediction_data}
    JSON response:
    """
    response = gemini_model.generate_content(prompt_template)
    return json.loads(response.text)

# --- API ENDPOINTS ---

@app.route('/api/test', methods=['GET'])
def test_api():
    """Simple endpoint to test if the API is running."""
    return jsonify({"status": "OK", "message": "API is running"}), 200

@app.route('/api/weather', methods=['POST'])
def get_weather_prediction():
    """Main API endpoint to handle the entire workflow."""
    try:
        data = request.get_json()
        user_prompt = data.get('prompt')
        if not user_prompt:
            return jsonify({"error": "Prompt is required"}), 400

        # Step 1: Parse the user prompt with Gemini
        parsed_info = parse_prompt_with_gemini(user_prompt)
        location = parsed_info.get("location")

        # Step 2: Get mock historical data
        historical_data = get_mock_weather_data(location)
        if not historical_data:
            return jsonify({"error": f"No mock data found for location: {location}"}), 404
        
        # Step 3: Get a prediction using mock function
        prediction = get_mock_prediction(historical_data)
        if not prediction:
            return jsonify({"error": "Could not generate prediction"}), 500
        
        raw_prediction_output = {
            "location": location,
            "predicted_temp_c": round(prediction[0][0], 1),
            "predicted_humidity_percent": round(prediction[0][1], 1)
        }

        # Step 4: Format the raw prediction into a user-friendly response with Gemini
        final_response = format_prediction_with_gemini(raw_prediction_output)

        return jsonify(final_response)

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run the app on port 3000, accessible from any IP
    app.run(host='0.0.0.0', port=5000)