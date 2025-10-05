import os
import re
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import date



genai.configure(api_key="AIzaSyBJABA-YfpktIoijmG4OGgBKJd0frglAXI")
gemini_model = genai.GenerativeModel('gemini-2.5-pro')

def clean_and_parse_json(text):
    """Extracts and parses JSON from Gemini's response, handling markdown formatting."""
    try:
        # First, try to parse directly
        return json.loads(text)
    except json.JSONDecodeError:
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
        
        # If all else fails, raise the original error
        raise json.JSONDecodeError(f"Could not parse JSON from: {text}")

def parse_prompt_with_gemini(user_prompt):
    # Get today's date
    today = date.today()
    # Format the date as dd-mm-yyyy
    formatted_date = today.strftime("%d-%m-%Y")

    """Uses Gemini to extract structured data from a user's natural language prompt."""
    prompt_template = f"""
    You are an AI assistant for a weather app. Extract the 'location' (both the longitude and latitude) and the "time frame" where they want the event to happen (in the format DD/MM/YYYY) from the user's request. The current day of today is "{formatted_date}" If you feel that you where not given enough information, please respond to the user asking for more information through the "complains" key.
    Respond ONLY with a valid JSON object containing a "longitude" key, "latitude" key, "time" key, and "complains" key. Do not include any markdown formatting.
    
    User request: "{user_prompt}"
    
    JSON output (no markdown, just the JSON):
    """
    print(f"🤖 PROMPT ENVIADO A GEMINI (parse_prompt):")
    print(f"   User input: {user_prompt}")
    
    response = gemini_model.generate_content(prompt_template)
    try:
        
        print(f"📥 RESPUESTA RAW DE GEMINI (parse_prompt):")
        print(f"   {response.text}")
        
        parsed_result = clean_and_parse_json(response.text)
        print(f"📊 DATOS PARSEADOS (parse_prompt):")
        print(f"   {parsed_result}")
        
        return parsed_result
    except Exception as e:
        print(f"❌ ERROR AL PARSEAR RESPUESTA DE GEMINI: {e}")
        print(f"📝 Respuesta completa: {response.text}")
        # Return a fallback
        return {'longitude': None, 'latitude': None, 'time': None, 'complains': "Por favor, especifique una ubicación más precisa, ya que hay varias ciudades con ese nombre."}  # Default fallback

def format_prediction_with_gemini(prediction_data):
    today = date.today()
    formatted_date = today.strftime("%d-%m-%Y")
    """Uses Gemini to convert raw ML model output into a user-friendly format."""
    prompt_template = f"""
    You are a helpful weather assistant. Based on the following raw prediction data, generate a user-friendly response in spanish. The current date is "{formatted_date}" in the format dd/mm/yyyy.
    The response must be a single, valid JSON object with one keys:
    1. "summary": A short, conversational paragraph.

    Do not include any markdown code block formatting in your response. Return only the JSON object.

    Prediction Data: {prediction_data}
    
    JSON response (no markdown, just the JSON):
    """
    print(f"🤖 PROMPT ENVIADO A GEMINI (format_prediction):")
    print(f"   Prediction Data: {prediction_data}")
    
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
        print(f"📝 Respuesta completa: {response.text}")
        # Return a fallback response
        return {
            "summary": f"Weather prediction for {prediction_data.get('location', 'unknown location')}: Temperature will be around {prediction_data.get('predicted_temp_c', 'N/A')}°C with {prediction_data.get('predicted_humidity_percent', 'N/A')}% humidity.",
            "table": f"| Metric | Value |\n|--------|-------|\n| Temperature | {prediction_data.get('predicted_temp_c', 'N/A')}°C |\n| Humidity | {prediction_data.get('predicted_humidity_percent', 'N/A')}% |"
        }
    
parse_prompt_with_gemini("Cual es la temperatura como")

#parse_prompt_with_gemini("Dame la temperatura de San Pedro dentro de un mes")
format_prediction_with_gemini({'Peticion original':"Quiero festejar una boda el siguiente mes en Monterrey por la tarde, debería hacerlo?", 'Tiempo':"04/11/2025", 'Temperatura':20, 'Precipitacion':2, 'Viento':3, 'Humedad':10, 'Cobertura de nubes':2, 'Probabilidad de tormenta electrica':0})


#https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/[location]/[date1]/[date2]?key=YOUR_API_KEY
#