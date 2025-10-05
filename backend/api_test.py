import os
import re
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import date, datetime, timedelta, timezone
import logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
OPEN_WEATHER_API_KEY = os.getenv("OPEN_WEATHER_API_KEY")

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-2.5-pro')

# --- HELPER FUNCTIONS FROM test.py ---

def convert_date_to_timestamp(date_str: str) -> int:
    """Convert a date string in dd/mm/yyyy format to Unix timestamp (UTC)."""
    try:
        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
        timestamp = int(date_obj.replace(tzinfo=timezone.utc).timestamp())
        logger.info(f"✅ Converted date {date_str} to timestamp {timestamp}")
        return timestamp
    except ValueError as e:
        logger.error(f"❌ Error converting date: {str(e)}")
        return None

def clean_and_parse_json(text):
    """Extracts and parses JSON from Gemini's response, handling markdown formatting."""
    try:
        # First, try to parse directly
        return json.loads(text.strip())
    except json.JSONDecodeError:
        try:
            # If that fails, try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
                return json.loads(json_text)
            
            # If no code block, try to find JSON-like content
            json_match = re.search(r'(\{[^}]*\})', text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
                return json.loads(json_text)
        except json.JSONDecodeError:
            pass
        
        # If all else fails, raise the original error
        raise json.JSONDecodeError(f"Could not parse JSON from: {text}", text, 0)

def parse_prompt_with_gemini(user_prompt):
    """Uses Gemini to extract structured data from a user's natural language prompt."""
    today = date.today()
    formatted_date = today.strftime("%d-%m-%Y")

    prompt_template = f"""
    You are an AI assistant for a weather app. Extract the 'location' (both the longitude and latitude) and the "time frame" where they want the event to happen (in the format DD/MM/YYYY) from the user's request. The current day of today is "{formatted_date}" If you feel that you where not given enough information, please respond to the user asking for more information through the "complains" key.
    Respond ONLY with a valid JSON object containing a "longitude" key, "latitude" key, "time" key, and "complains" key. Do not include any markdown formatting.
    
    User request: "{user_prompt}"
    
    JSON output (no markdown, just the JSON):
    """
    
    print(f"🤖 PROMPT ENVIADO A GEMINI (parse_prompt):")
    print(f"   User input: {user_prompt}")
    
    try:
        response = gemini_model.generate_content(prompt_template)
        
        print(f"📥 RESPUESTA RAW DE GEMINI (parse_prompt):")
        print(f"   {response.text}")
        
        parsed_result = clean_and_parse_json(response.text)
        #print(f"📊 DATOS PARSEADOS (parse_prompt):")
        #print(f"   {parsed_result}")
        
        return parsed_result
        
    except Exception as e:
        print(f"❌ ERROR AL PARSEAR RESPUESTA DE GEMINI: {e}")
        print(f"📝 Respuesta completa: {response.text if 'response' in locals() else 'No response'}")
        # Return a fallback
        return {'longitude': None, 'latitude': None, 'time': None, 'complains': "Por favor, especifique una ubicación más precisa."}

def get_weather_data(lat: float, lon: float, dt: str) -> dict:
    try:
        # Construct API URL
        base_url = "https://api.openweathermap.org/data/2.5/forecast"
        week_gotten = {'week': []}
        params = {
                'lat': lat,
                'lon': lon,
                'units': 'metric',  # Use metric units
                'appid': OPEN_WEATHER_API_KEY
        }

        logger.info(f"🌍 Fetching weather data for coordinates: {lat}, {lon}")
            
            # Make API request
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise exception for bad status codes
            
        data = response.json()
            
            # Extract relevant data for ML model
        processed_data = {'week': []}
        for i in range(len(data['list'])):
            item = data['list'][i]
            date = datetime.fromtimestamp(item['dt'] + i*86400).strftime('%Y-%m-%d')
            
            day_data = {
                'day': {
                    'date': date,
                    'temp': item['main']['temp'],
                    'humidity': item['main']['humidity'],
                }
            }
            processed_data['week'].append(day_data)

        
            
        logger.info("✅ Weather data fetched successfully")
        return processed_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching weather data: {str(e)}")
        return {
            'error': f"Error fetching weather data: {str(e)}",
            'status': 'error'
        }

def format_prediction_with_gemini(prediction_data):
    """Uses Gemini to convert raw weather data into a user-friendly format."""
    prompt_template = f"""
    You are a helpful weather assistant. Based on the following weather data, generate a user-friendly response for the user's request.
    The response must be a single, valid JSON object with two keys:
    1. "interpretation": A short, conversational paragraph in Spanish explaining the weather conditions and recommendations.
    2. "precipitation": The predicted precipitation that was found in the prediction data. 


    Do not include any markdown code block formatting in your response. Return only the JSON object.

    Weather Data: {prediction_data}
    
    JSON response (no markdown, just the JSON):
    """
    
    print(f"🤖 PROMPT ENVIADO A GEMINI (format_prediction):")
    print(f"   Weather Data: {prediction_data}")
    
    try:
        response = gemini_model.generate_content(prompt_template)
        
        print(f"📥 RESPUESTA RAW DE GEMINI (format_prediction):")
        print(f"   {response.text}")
        
        formatted_result = clean_and_parse_json(response.text)
        print(f"📊 DATOS FORMATEADOS (format_prediction):")
        print(f"   {formatted_result}")
        
        return formatted_result
        
    except Exception as e:
        print(f"❌ ERROR AL FORMATEAR RESPUESTA DE GEMINI: {e}")
        print(f"📝 Respuesta completa: {response.text if 'response' in locals() else 'No response'}")
        # Return a fallback response
        weather_data = prediction_data.get('weather_data', {})
        location = f"{weather_data.get('city_name', 'Unknown')}, {weather_data.get('country', 'Unknown')}"
        temp = weather_data.get('temp', 'N/A')
        humidity = weather_data.get('humidity', 'N/A')
        description = weather_data.get('description', 'N/A')
        
        return {
            "summary": f"El clima en {location} presenta una temperatura de {temp}°C con {description}. La humedad es del {humidity}%.",
            "table": f"| Métrica | Valor |\n|---------|-------|\n| Temperatura | {temp}°C |\n| Humedad | {humidity}% |\n| Descripción | {description} |"
        }



# --- API ENDPOINTS ---

@app.route('/api/weather', methods=['POST'])
def weather_endpoint():
    """Main API endpoint that receives prompt from frontend and returns formatted weather prediction."""
    try:
        print(f"\n🌟 === INICIO DE NUEVA PETICIÓN DESDE FRONTEND ===")
        
        # Get JSON data from request
        data = request.get_json()
        user_prompt = data.get('prompt')
        
        if not user_prompt:
            return jsonify({'error': 'Se requiere un prompt'}), 400

        print(f"🔍 Prompt del usuario: {user_prompt}")

        

        # PASO 1: Procesar el prompt con Gemini para extraer ubicación y fecha
        print(f"\n📍 PASO 1: Parseando prompt del usuario con Gemini...")
        parsed_result = parse_prompt_with_gemini(user_prompt)
        
        # Check if Gemini found any issues with the prompt
        if parsed_result.get('complains'):
            print(f"❌ Gemini tiene una queja: {parsed_result['complains']}")
            return jsonify({
                'error': parsed_result['complains']
            }), 400

        lat = parsed_result.get('latitude')
        lon = parsed_result.get('longitude')
        dt = parsed_result.get('time')

        if not all([lat, lon, dt]):
            print(f"❌ No se pudo extraer información completa: lat={lat}, lon={lon}, dt={dt}")
            return jsonify({
                'error': 'No se pudo extraer la información necesaria del prompt',
                'details': parsed_result
            }), 400

        print(f"📍 Ubicación extraída: Lat={lat}, Lon={lon}, Fecha={dt}")

        # PASO 2: Consultar OpenWeather API
        print(f"\n📊 PASO 2: Consultando OpenWeather API...")
        weather_data = get_weather_data(
            round(float(lat), 2),
            round(float(lon), 2),
            dt
        )

        if weather_data.get('error'):
            print(f"❌ Error en OpenWeather: {weather_data['error']}")
            return jsonify({'error': weather_data['error']}), 500

        print(f"📊 Datos del clima obtenidos exitosamente")

        # Normalize backend response to an object the frontend expects
        week = weather_data.get('week', []) if isinstance(weather_data, dict) else []

        # Compute a simple representative temperature (first entry or average)
        temp_val = None
        if week:
            try:
                temps = [d.get('day', {}).get('temp') for d in week if d.get('day', {}).get('temp') is not None]
                precipitation = [d.get('day', {}).get('humidity') for d in week if d.get('day', {}).get('humidity') is not None]
                print(precipitation)
                if temps:
                    # average temperature
                    temp_val = round(sum(temps) / len(temps), 1)
                if precipitation:
                    precipitation_val = round(sum(precipitation_val)/len(precipitation), 1)
                    print("Ran this")
            except Exception:
                temp_val = None
                precipitation_val = None

        # Ensure we always provide sensible fallbacks so frontend doesn't show N/A
        response_payload = {
            'lat': lat,
            'lon': lon,
            'temperature': temp_val if temp_val is not None else 20,  # fallback 20°C
            'precipitation': precipitation_val if precipitation_val is not None else 20,
            'gemini': '',
            'week': week
        }

        # PASO 3: Formatear la respuesta final con Gemini
        print(f"\n✨ PASO 3: Formateando respuesta final con Gemini...")
        final_response = format_prediction_with_gemini({
            'original_prompt': user_prompt,
            'location': f"Lat: {lat}, Lon: {lon}",
            'date': dt,
            'precipitation': response_payload['precipitation']
        })
        print(f"\n🎯 === RESPUESTA FINAL ENVIADA AL FRONTEND ===")
        print(f"🌟 === FIN DE PETICIÓN ===\n")

        return jsonify(final_response)

    except Exception as e:
        print(f"💥 ERROR GENERAL EN EL ENDPOINT: {str(e)}")
        logger.error(f"Error en el endpoint: {str(e)}")
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint to verify API is running."""
    return jsonify({
        'status': 'OK', 
        'message': 'NASA Space Apps Weather API is running! 🚀',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'weather': 'POST /api/weather',
            'test': 'GET /api/test'
        }
    }), 200

if __name__ == '__main__':
    # Run the Flask app
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 === INICIANDO SERVIDOR NASA SPACE APPS ===")
    print(f"🔧 Puerto: {port}")
    print(f"🔑 Gemini API Key configurado: {'✅' if os.getenv('GEMINI_API_KEY') else '❌'}")
    print(f"🌤️ OpenWeather API Key configurado: {'✅' if OPEN_WEATHER_API_KEY else '❌'}")
    print(f"📡 Endpoints disponibles:")
    print(f"   POST http://localhost:{port}/api/weather")
    print(f"   GET  http://localhost:{port}/api/test")
    print(f"🌟 === SERVIDOR LISTO PARA CONECTAR CON FRONTEND ===\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)