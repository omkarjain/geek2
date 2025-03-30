import logging
from flask import Flask, request, render_template
from markupsafe import Markup
import requests
import os
import google.generativeai as genai

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Setup Gemini API for Itinerary Generation
def setup_gemini_api():
    logging.info("setup_gemini_api called")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY environment variable not set.")
        raise ValueError("Please set the GEMINI_API_KEY environment variable.")
    genai.configure(api_key=api_key)
    logging.info("Gemini API configured successfully.")
    return genai.GenerativeModel('gemini-1.5-flash')

# Generate Itinerary
def generate_itinerary_with_gemini(user_inputs, model):
    logging.info("generate_itinerary_with_gemini called")
    destination = user_inputs["destination"]
    days = user_inputs["days"]
    budget = user_inputs["budget"]
    cuisine_preference = user_inputs["cuisine_preference"]
    people_number = user_inputs["people_number"]
    interests = user_inputs["interests"]
    budget_per_day = budget / days / people_number

    prompt = (
        f"Generate a visually appealing {days}-day travel itinerary for {destination}. "
        f"The budget is ${budget} for {people_number} people, approximately ${budget_per_day:.2f} per person per day. "
        f"The user prefers {cuisine_preference or 'no specific'} cuisine and is interested in {interests}. "
        f"Use bullet points or numbered lists for activities and dining recommendations. "
        f"Include estimated times, descriptions, and total daily costs.\n"
        f"**Day 1:**\n"
        f"- Morning (9:00 AM - 12:00 PM): [Activity] - [Description] - [Cost]\n"
        f"- Lunch (12:00 PM - 1:00 PM): [Dining recommendation] - [Cost]\n"
        f"- Afternoon (1:00 PM - 5:00 PM): [Activity] - [Description] - [Cost]\n"
        f"- Evening (7:00 PM onwards): [Activity/Dinner] - [Cost]\n"
        f"**Total Estimated Day 1 Cost:** [Total Cost]\n\n"
        f"... Continue for each day."
    )

    try:
        response = model.generate_content(prompt)
        logging.info(f"Gemini API response: {response.text}")
        return response.text
    except Exception as e:
        logging.error(f"Gemini API error: {e}")
        return f"An error occurred during API call: {e}"

# Nominatim (OpenStreetMap) Geocoding
def get_coordinates(address):
    logging.info(f"get_coordinates called with address: {address}")
    url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json"
    headers = {'User-Agent': 'ItineraryGenerator/1.0'}
    try:
        response = requests.get(url, headers=headers)
        logging.info(f"Nominatim response: {response.text}")
        data = response.json()
        if data:
            logging.info(f"Coordinates found: {data[0]['lat']}, {data[0]['lon']}")
            return data[0]["lat"], data[0]["lon"]
        else:
            logging.info("Coordinates not found.")
            return None, None
    except Exception as e:
        logging.error(f"Nominatim error: {e}")
        return None, None

# Flask Route for Itinerary Generation
@app.route('/', methods=['GET', 'POST'])
def itinerary_generator():
    logging.info("itinerary_generator route called")
    if request.method == 'POST':
        user_inputs = {
            "origin": request.form['origin'],
            "destination": request.form['destination'],
            "days": int(request.form['days']),
            "budget": float(request.form['budget']),
            "cuisine_preference": request.form['cuisine_preference'],
            "people_number": int(request.form['people_number']),
            "interests": request.form['interests'],
        }
        logging.info(f"User inputs: {user_inputs}")

        model = setup_gemini_api()
        itinerary = generate_itinerary_with_gemini(user_inputs, model)
        logging.info(f"Generated itinerary: {itinerary}")

        origin_lat, origin_lon = get_coordinates(user_inputs["origin"])
        logging.info(f"Origin coordinates: {origin_lat}, {origin_lon}")
        dest_lat, dest_lon = get_coordinates(user_inputs["destination"])
        logging.info(f"Destination coordinates: {dest_lat}, {dest_lon}")

        return render_template(
            'index.html',
            itinerary=Markup(itinerary.replace('\n', '<br>')),
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            dest_lat=dest_lat,
            dest_lon=dest_lon,
        )

    return render_template('index.html', itinerary=None, origin_lat=None, origin_lon=None, dest_lat=None, dest_lon=None)

if __name__ == '__main__':
    app.run(debug=True)
