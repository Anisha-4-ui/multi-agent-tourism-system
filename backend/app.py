from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
app = Flask(__name__)
CORS(app)

def extract_place_name(user_input):
    """
    Extract place name from user's full sentence
    """
    if not user_input:
        return None
    
    # Common phrases that indicate a place name follows
    patterns = [
        "going to go to",
        "going to", 
        "visit",
        "travel to",
        "plan my trip to",
        "i'm going to",
        "i am going to",
        "what is the weather in",
        "what are the places in",
        "what can i visit in"
    ]
    
    user_input_lower = user_input.lower()
    
    # Try to find and extract place after these patterns
    for pattern in patterns:
        if pattern in user_input_lower:
            # Extract everything after the pattern
            start_index = user_input_lower.find(pattern) + len(pattern)
            place_candidate = user_input[start_index:].strip()
            
            # Clean up: remove punctuation and trailing words
            place_candidate = place_candidate.split('.')[0].split('?')[0].split(',')[0].strip()
            
            if place_candidate:
                return place_candidate.title()
    
    # If no pattern found, return the original input as fallback
    return user_input.strip().title()

def get_coordinates(place_name):
    """
    Get latitude and longitude for a place using Nominatim API
    """
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': place_name,
            'format': 'json',
            'limit': 1
        }
        headers = {
            'User-Agent': 'TourismApp/1.0'
        }
        
        print(f"DEBUG: Fetching coordinates for '{place_name}'")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            print(f"DEBUG: Found coordinates: {lat}, {lon}")
            return lat, lon
        else:
            print(f"DEBUG: No coordinates found for '{place_name}'")
            return None, None
    except Exception as e:
        print(f"ERROR in get_coordinates: {e}")
        return None, None

def get_weather(lat, lon):
    """
    Get current weather using Open-Meteo API
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': lat,
            'longitude': lon,
            'current': 'temperature_2m,precipitation_probability',
            'timezone': 'auto'
        }
        
        print(f"DEBUG: Fetching weather for coordinates {lat}, {lon}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        current = data.get('current', {})
        
        temp = current.get('temperature_2m', 'N/A')
        rain_chance = current.get('precipitation_probability', 'N/A')
        
        weather_info = f"It's currently {temp}°C with a {rain_chance}% chance of rain."
        print(f"DEBUG: Weather info: {weather_info}")
        return weather_info
        
    except Exception as e:
        print(f"ERROR in get_weather: {e}")
        return "Weather information is currently unavailable."

def get_places(lat, lon):
    """
    Get tourist places using Overpass API
    """
    try:
        overpass_query = f"""
        [out:json];
        (
          node["tourism"](around:10000,{lat},{lon});
          node["historic"](around:10000,{lat},{lon});
          node["leisure"](around:10000,{lat},{lon});
        );
        out 5;
        """
        
        url = "https://overpass-api.de/api/interpreter"
        response = requests.post(url, data={'data': overpass_query}, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        places = []
        
        for element in data.get('elements', []):
            if 'tags' in element and 'name' in element['tags']:
                places.append(element['tags']['name'])
        
        print(f"DEBUG: Found {len(places)} places: {places}")
        return places[:5]  # Return top 5 places
        
    except Exception as e:
        print(f"ERROR in get_places: {e}")
        return ["Unable to fetch places at the moment."]

@app.route("/tourism", methods=["POST"])
def tourism():
    try:
        data = request.json
        user_input = data.get("place", "").strip()
        
        print(f"=== DEBUG: REQUEST RECEIVED ===")
        print(f"Full user input: '{user_input}'")
        
        # Extract place name from the full sentence
        place_name = extract_place_name(user_input)
        print(f"Extracted place name: '{place_name}'")
        
        if not place_name:
            return jsonify({"answer": "I don't think this place exists. Try another place."})
        
        # Get coordinates
        lat, lon = get_coordinates(place_name)
        
        if lat is None or lon is None:
            return jsonify({"answer": f"I don't think '{place_name}' exists. Try another place."})
        
        response = ""

        # Check if user asked about weather
        user_input_lower = user_input.lower()
        print(f"DEBUG: User input lower: '{user_input_lower}'")
        
        # More specific weather keywords - only when they're asking about weather
        weather_keywords = [
            'temperature', 'weather', 'rain', 'hot', 'cold', 'degree', 
            'how hot', 'how cold', 'climate'
        ]
        wants_weather = any(keyword in user_input_lower for keyword in weather_keywords)
        
        # More specific places keywords - exclude common verbs like "go"
        places_keywords = [
            'place', 'visit', 'attraction', 'tourist', 'sightseeing',
            'things to do', 'what to see', 'where to go', 'tourist spot'
        ]
        wants_places = any(keyword in user_input_lower for keyword in places_keywords)
        
        print(f"DEBUG: Weather keywords found: {[kw for kw in weather_keywords if kw in user_input_lower]}")
        print(f"DEBUG: Places keywords found: {[kw for kw in places_keywords if kw in user_input_lower]}")
        print(f"DEBUG: wants_weather={wants_weather}, wants_places={wants_places}")
        
        # ONLY get weather if specifically asked
        if wants_weather and not wants_places:
            print("DEBUG: Getting ONLY weather information")
            weather_info = get_weather(lat, lon)
            response = f"In {place_name}, {weather_info}"
        
        # ONLY get places if specifically asked  
        elif wants_places and not wants_weather:
            print("DEBUG: Getting ONLY places information")
            places = get_places(lat, lon)
            if places and len(places) > 0:
                response = "These are the places you can go:\n" + "\n".join(f"- {place}" for place in places)
            else:
                response = "No popular tourist places found for this location."
        
        # Get both if both are asked
        elif wants_weather and wants_places:
            print("DEBUG: Getting BOTH weather and places")
            weather_info = get_weather(lat, lon)
            places = get_places(lat, lon)
            response = f"In {place_name}, {weather_info}\n\n"
            if places and len(places) > 0:
                response += "These are the places you can go:\n" + "\n".join(f"- {place}" for place in places)
            else:
                response += "No popular tourist places found for this location."
        
        # If user didn't specify anything, provide both but mention it
        else:
            print("DEBUG: No specific request - providing both with explanation")
            weather_info = get_weather(lat, lon)
            places = get_places(lat, lon)
            response = f"In {place_name}, {weather_info}\n\n"
            if places and len(places) > 0:
                response += "These are the places you can go:\n" + "\n".join(f"- {place}" for place in places)

        print(f"DEBUG: Final response: '{response}'")
        return jsonify({"answer": response})
        
    except Exception as e:
        print(f"ERROR in tourism route: {e}")
        return jsonify({"answer": "Sorry, there was an error processing your request. Please try again."})

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Tourism Multi-Agent System is running!"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Tourism Multi-Agent System on port {port}...")
    app.run(host='0.0.0.0', port=port)
