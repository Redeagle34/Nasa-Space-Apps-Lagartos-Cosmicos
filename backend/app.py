import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai
import snowflake.connector
import joblib # Used to load the pre-trained ML model

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
ml_model = joblib.load('weather_model.pkl')

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

def get_data_from_snowflake(location):
    """Connects to Snowflake and fetches historical weather data for the ML model."""
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse="COMPUTE_WH",
        database="WEATHER_DATA",
        schema="PUBLIC"
    )
    try:
        cs = conn.cursor()
        query = f"SELECT TEMPERATURE_C, HUMIDITY_PERCENT, WIND_SPEED_KPH FROM HOURLY_RECORDS WHERE LOCATION_NAME = '{location}' ORDER BY RECORDED_AT DESC LIMIT 168;" # Get last 7 days of data
        cs.execute(query)
        # Assuming your model needs a list of tuples or a similar format
        return cs.fetchall()
    finally:
        cs.close()
        conn.close()

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

# --- API ENDPOINT ---

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

        # Step 2: Get historical data from Snowflake
        historical_data = get_data_from_snowflake(location)
        if not historical_data:
            return jsonify({"error": f"No data found for location: {location}"}), 404
        
        # Step 3: Get a prediction from the ML model
        # Note: The input to predict() must match what your model was trained on.
        # This is a simplified example. You may need to reshape or process the data.
        prediction = ml_model.predict([historical_data[0]]) # Example: predict using the most recent data point
        
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
        return jsonify({"error": "An internal server error occurred"}), 500

if __name__ == '__main__':
    # Run the app on port 3000, accessible from any IP
    app.run(host='0.0.0.0', port=5000)