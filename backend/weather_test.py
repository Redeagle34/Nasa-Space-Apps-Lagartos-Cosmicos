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

def parse_prompt_with_gemini(user_prompt, temperature, precipitation):
    """Uses Gemini to extract structured data from a user's natural language prompt."""
    today = date.today()
    formatted_date = today.strftime("%d-%m-%Y")

    prompt_template = f"""
    You are a helpful weather assistant. Based on the following weather data, generate a user-friendly response for the user's request.
    The response must be a single, valid JSON object with two keys:
    1. "interpretation": A short, conversational paragraph in Spanish explaining the weather conditions and recommendations.
    
    User request: "{user_prompt}"
    Temperature: "{temperature}"
    Precipitation: "{precipitation}"
    
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
    
@app.route('/api/weather', methods=['POST'])
def weather_endpoint():
    """Main API endpoint that receives prompt from frontend and returns formatted weather prediction."""
    try:
        print(f"\n🌟 === INICIO DE NUEVA PETICIÓN DESDE FRONTEND ===")
        
        # Get JSON data from request
        data = request.get_json()
        user_prompt = data.get('prompt')
        temperature = data.get('teperature')
        precipitation = data.get('precipitation')
        
        if not user_prompt:
            return jsonify({'error': 'Se requiere un prompt'}), 400

        print(f"🔍 Prompt del usuario: {user_prompt}")

        

        # PASO 1: Procesar el prompt con Gemini para extraer ubicación y fecha
        print(f"\n📍 PASO 1: Parseando prompt del usuario con Gemini...")
        parsed_result = parse_prompt_with_gemini(user_prompt, temperature, precipitation)


        # PASO 3: Formatear la respuesta final con Gemini
    
        print(f"\n🎯 === RESPUESTA FINAL ENVIADA AL FRONTEND ===")
        print(f"🌟 === FIN DE PETICIÓN ===\n")

        return jsonify(parsed_result)

    except Exception as e:
        print(f"💥 ERROR GENERAL EN EL ENDPOINT: {str(e)}")
        logger.error(f"Error en el endpoint: {str(e)}")
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

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