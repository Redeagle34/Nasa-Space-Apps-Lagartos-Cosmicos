import os
import re
import json
import requests
import time 
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import date, datetime, timedelta, timezone
import logging

# Load environment variables
load_dotenv()
OPEN_WEATHER_API_KEY = os.getenv('OPEN_WEATHER_API_KEY')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_date_to_timestamp(date_str: str) -> int:
    """
    Convert a date string in dd/mm/yyyy format to Unix timestamp (UTC).
    """
    try:
        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
        timestamp = int(date_obj.replace(tzinfo=timezone.utc).timestamp())
        logger.info(f"✅ Converted date {date_str} to timestamp {timestamp}")
        return timestamp
    except ValueError as e:
        logger.error(f"❌ Error converting date: {str(e)}")
        return None

def get_historical_weather(lat: float, lon: float, date_str: str) -> list:
    """
    Fetch historical weather data for 7 days before the given date.
    """
    historical_data = []
    try:
        # Convert target date to datetime
        target_date = datetime.strptime(date_str, "%d/%m/%Y")
        
        # Get data for past 7 days
        for i in range(7):
            current_date = target_date - timedelta(days=i)
            base_url = "https://api.openweathermap.org/data/2.5/weather"
            
            params = {
                'lat': lat,
                'lon': lon,
                'units': 'metric',
                'appid': OPEN_WEATHER_API_KEY,
                'dt': int(current_date.replace(tzinfo=timezone.utc).timestamp())
            }
            
            logger.info(f"📅 Fetching data for date: {current_date.strftime('%d/%m/%Y')}")
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            daily_data = response.json()
            
            processed_daily = {
                'date': current_date.strftime('%Y-%m-%d'),
                'temp': {
                    'current': daily_data['main']['temp'],
                    'min': daily_data['main']['temp_min'],
                    'max': daily_data['main']['temp_max']
                },
                'humidity': daily_data['main']['humidity'],
                'precipitation': daily_data.get('rain', {}).get('1h', 0),
                'wind_speed': daily_data['wind']['speed'],
                'description': daily_data['weather'][0]['description']
            }
            
            historical_data.append(processed_daily)
            time.sleep(1)  # Avoid rate limiting
            
        logger.info(f"✅ Successfully fetched historical data for {len(historical_data)} days")
        return historical_data
        
    except Exception as e:
        logger.error(f"❌ Error fetching historical data: {str(e)}")
        return []

def get_weather_data(lat: float, lon: float, dt: str) -> dict:
    """
    Enhanced weather data fetching with historical data.
    """
    try:
        # Get current weather
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'units': 'metric',
            'appid': OPEN_WEATHER_API_KEY
        }
        
        logger.info(f"🌍 Fetching current weather for: {lat}, {lon}")
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        current_data = response.json()
        
        # Get historical data
        historical = get_historical_weather(lat, lon, dt)
        
        # Process and structure the response
        processed_data = {
            'current': {
                'temp': current_data['main']['temp'],
                'humidity': current_data['main']['humidity'],
                'precipitation': current_data.get('rain', {}).get('1h', 0),
                'description': current_data['weather'][0]['description'],
                'wind_speed': current_data['wind']['speed']
            },
            'daily': historical
        }
        
        logger.info("✅ Weather data processed successfully")
        logger.info(f"📊 Data structure: {json.dumps(processed_data, indent=2, ensure_ascii=False)}")
        
        return processed_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error in get_weather_data: {str(e)}")
        return {
            'error': str(e),
            'status': 'error'
        }

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
gemini_model = genai.GenerativeModel('gemini-pro')

def clean_and_parse_json(text):
    """Extracts and parses JSON from Gemini's response."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        json_match = re.search(r'(\{[^}]*\})', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        raise json.JSONDecodeError(f"Could not parse JSON from: {text}")

def parse_prompt_with_gemini(user_prompt):
    """Extract location and time from user prompt."""
    today = date.today()
    formatted_date = today.strftime("%d-%m-%Y")
    
    prompt_template = f"""
    You are an AI assistant for a weather app. Extract the 'location' (both the longitude and latitude) 
    and the "time frame" where they want the event to happen (in the format DD/MM/YYYY) from the user's request. 
    The current day of today is "{formatted_date}".
    
    Respond ONLY with a valid JSON object containing "longitude", "latitude", "time", and "complains" keys.
    
    User request: "{user_prompt}"
    """
    
    logger.info(f"🤖 Processing prompt: {user_prompt}")
    
    response = gemini_model.generate_content(prompt_template)
    try:
        parsed_result = clean_and_parse_json(response.text)
        logger.info(f"📊 Parsed result: {json.dumps(parsed_result, indent=2)}")
        return parsed_result
    except Exception as e:
        logger.error(f"❌ Error parsing Gemini response: {e}")
        return {
            'longitude': None,
            'latitude': None,
            'time': None,
            'complains': "Por favor, especifique una ubicación más precisa."
        }

# Test the enhanced implementation
if __name__ == "__main__":
    test_prompts = [
        "Cual es la temperatura en Monterrey México mañana",
        "Como estará el clima en Ciudad de México el próximo mes",
    ]
    
    for prompt in test_prompts:
        print(f"\n🔍 Testing prompt: {prompt}")
        parsed_result = parse_prompt_with_gemini(prompt)
        
        if parsed_result.get('latitude') and parsed_result.get('longitude'):
            weather_data = get_weather_data(
                round(float(parsed_result['latitude']), 2),
                round(float(parsed_result['longitude']), 2),
                parsed_result.get('time')
            )
            
            print("\n📊 Weather Data Results:")
            print(json.dumps(weather_data, indent=2, ensure_ascii=False))
        else:
            print("❌ No valid coordinates found in parsed result")