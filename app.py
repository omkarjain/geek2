from flask import Flask, request, render_template
from markupsafe import Markup
import requests  # For Nominatim

app = Flask(__name__)

# Setup Gemini API for Itinerary Generation
def setup_gemini_api():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Please set the GEMINI_API_KEY environment variable.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

# Generate Itinerary
def generate_itinerary_with_gemini(user_inputs, model):
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
        return response.text
    except Exception as e:
        return f"An error occurred during API call: {e}"

# Nominatim (OpenStreetMap) Geocoding
def get_coordinates(address):
    """Gets coordinates from an address using Nominatim."""
    url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json"
    headers = {'User-Agent': 'ItineraryGenerator/1.0'} # Replace with your app name
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        if data:
            return data[0]["lat"], data[0]["lon"]
        else:
            return None, None
    except Exception as e:
        return None, None

# Flask Route for Itinerary Generation
@app.route('/', methods=['GET', 'POST'])
def itinerary_generator():
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

        model = setup_gemini_api()
        itinerary = generate_itinerary_with_gemini(user_inputs, model)
        origin_lat, origin_lon = get_coordinates(user_inputs["origin"])
        dest_lat, dest_lon = get_coordinates(user_inputs["destination"])

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
    app.run(debug=True)  # Remove debug=True for production
