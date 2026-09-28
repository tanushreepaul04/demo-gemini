# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import datetime
import json
import os
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from zoneinfo import ZoneInfo

import google.genai as genai
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore, storage
from google.genai import types

from .a2ui_utils import a2ui_callback


PROJECT_ID = "qwiklabs-gcp-01-19d6c0b95c76"
BUCKET_NAME = "travel-concierge-assets-qwiklabs-gcp-01-19d6c0b95c76"
MEMORY_BANK_ID = "2137529219477929984"


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback after turn to extract and store durable memories into Memory Bank."""
    await callback_context.add_session_to_memory()
    return None


memory_service = VertexAiMemoryBankService(
    project=PROJECT_ID,
    location="us-central1",
    agent_engine_id=MEMORY_BANK_ID,
)



def get_code_executor() -> AgentEngineSandboxCodeExecutor:
    """Helper to initialize AgentEngineSandboxCodeExecutor using deployment_metadata.json if available."""
    metadata_file = Path(__file__).parent.parent / "deployment_metadata.json"
    sandbox_id = None
    engine_id = None
    if metadata_file.exists():
        try:
            with open(metadata_file) as f:
                data = json.load(f)
            sandbox_id = data.get("sandbox_resource_name")
            engine_id = data.get("remote_agent_runtime_id")
        except Exception:
            pass

    if sandbox_id:
        return AgentEngineSandboxCodeExecutor(sandbox_resource_name=sandbox_id)
    elif engine_id:
        return AgentEngineSandboxCodeExecutor(agent_engine_resource_name=engine_id)
    else:
        return AgentEngineSandboxCodeExecutor()



def get_firestore_client() -> firestore.Client:
    """Returns a Firestore client configured with the explicit project ID."""
    return firestore.Client(project=PROJECT_ID)


def list_destinations(category: str = "") -> str:
    """List or search travel destinations from the Firestore catalog.

    Args:
        category: Optional category filter (e.g. 'Culture & Heritage', 'Beach & Relaxation', 'Mountain & Adventure').

    Returns:
        A string formatted list of matching destinations.
    """
    db = get_firestore_client()
    docs = db.collection("destinations").stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        if category:
            if category.lower() not in data.get("category", "").lower():
                continue
        results.append(data)
    if not results:
        return f"No destinations found matching category '{category}'." if category else "No destinations found in database."

    formatted = []
    for d in results:
        formatted.append(
            f"- ID: {d.get('id')}\n"
            f"  Name: {d.get('name')} ({d.get('country')})\n"
            f"  Category: {d.get('category')} | Budget: {d.get('budget_tier')}\n"
            f"  Description: {d.get('description')}\n"
            f"  Best Time: {d.get('best_time_to_visit')}"
        )
    return "\n\n".join(formatted)


def get_destination(destination_id: str) -> str:
    """Retrieve full details for a specific travel destination by ID.

    Args:
        destination_id: The unique ID of the destination (e.g. 'kyoto-japan', 'santorini-greece').

    Returns:
        A string formatted summary of the destination details.
    """
    db = get_firestore_client()
    doc_ref = db.collection("destinations").document(destination_id)
    doc = doc_ref.get()
    if not doc.exists:
        return f"Destination with ID '{destination_id}' not found."
    data = doc.to_dict()
    activities = ", ".join(data.get("top_activities", []))
    return (
        f"Destination Details for {data.get('name')} ({data.get('id')}):\n"
        f"Country: {data.get('country')}\n"
        f"Category: {data.get('category')}\n"
        f"Budget Tier: {data.get('budget_tier')}\n"
        f"Description: {data.get('description')}\n"
        f"Top Activities: {activities}\n"
        f"Best Time to Visit: {data.get('best_time_to_visit')}"
    )


def add_destination(
    destination_id: str,
    name: str,
    country: str,
    category: str,
    budget_tier: str,
    description: str,
    best_time_to_visit: str = "",
) -> str:
    """Add a new travel destination to the Firestore catalog.

    Args:
        destination_id: Unique slug ID for the destination (e.g. 'paris-france').
        name: Name of the destination city or location.
        country: Country where the destination is located.
        category: Travel category (e.g., 'Culture & Heritage', 'Beach & Relaxation').
        budget_tier: Budget tier indicator (e.g., '$', '$$', '$$$', '$$$$').
        description: Brief overview of the destination.
        best_time_to_visit: Recommended season or months to visit.

    Returns:
        Confirmation message of creation.
    """
    db = get_firestore_client()
    doc_data = {
        "id": destination_id,
        "name": name,
        "country": country,
        "category": category,
        "budget_tier": budget_tier,
        "description": description,
        "best_time_to_visit": best_time_to_visit,
        "top_activities": [],
    }
    db.collection("destinations").document(destination_id).set(doc_data)
    return f"Successfully added destination '{name}' ({destination_id}) to Firestore."


def get_live_weather(location: str) -> str:
    """Fetches real-time live weather and temperature for any city or destination worldwide using Open-Meteo.

    Args:
        location: The name of the city, region, or destination (e.g. 'Tokyo', 'Paris', 'New York', 'Banff').

    Returns:
        A string with live temperature (°C and °F) and current wind speed.
    """
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(location)}&count=1"
        req = urllib.request.Request(geo_url, headers={"User-Agent": "TravelConcierge/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            geo_data = json.loads(resp.read().decode())
        if not geo_data.get("results"):
            return f"Could not find coordinates for location: '{location}'."
        place = geo_data["results"][0]
        lat, lon = place["latitude"], place["longitude"]
        city_name = place.get("name", location)
        country = place.get("country", "")

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        req2 = urllib.request.Request(weather_url, headers={"User-Agent": "TravelConcierge/1.0"})
        with urllib.request.urlopen(req2, timeout=5) as resp2:
            w_data = json.loads(resp2.read().decode())
        cw = w_data.get("current_weather", {})
        temp_c = cw.get("temperature")
        temp_f = round(temp_c * 9 / 5 + 32, 1) if temp_c is not None else "N/A"
        wind = cw.get("windspeed")
        return f"Current live weather in {city_name}, {country}: {temp_c}°C ({temp_f}°F), wind speed {wind} km/h."
    except Exception as e:
        return f"Unable to fetch live weather for '{location}': {str(e)}"


def convert_currency(amount: float, from_currency: str = "USD", to_currency: str = "EUR") -> str:
    """Converts a monetary amount between currencies using live European Central Bank exchange rates.

    Args:
        amount: The monetary amount to convert (e.g. 500.0).
        from_currency: 3-letter source currency code (e.g. 'USD', 'EUR', 'GBP').
        to_currency: 3-letter target currency code (e.g. 'JPY', 'EUR', 'CAD', 'AUD').

    Returns:
        A string with the converted value and exchange rate.
    """
    try:
        api_key = os.getenv("CURRENCY_API_KEY", "")
        from_curr = from_currency.upper()
        to_curr = to_currency.upper()

        url = f"https://api.frankfurter.dev/v1/latest?amount={amount}&from={from_curr}&to={to_curr}"
        headers = {"User-Agent": "TravelConcierge/1.0"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        rates = data.get("rates", {})
        if to_curr not in rates:
            return f"Conversion rate from {from_curr} to {to_curr} is not available."
        converted = rates[to_curr]
        rate = round(converted / amount, 4) if amount else 0
        return (
            f"{amount} {from_curr} = {converted:.2f} {to_curr} "
            f"(Exchange Rate: 1 {from_curr} = {rate} {to_curr} as of {data.get('date')})"
        )
    except Exception as e:
        return f"Unable to convert currency from {from_currency} to {to_currency}: {str(e)}"


def geocode_address(address: str) -> str:
    """Geocodes an address or landmark into geographic coordinates (latitude and longitude) using Google Geocoding API.

    Args:
        address: The address, location, or landmark name to geocode (e.g. 'Kiyomizu-dera, Kyoto', 'Eiffel Tower, Paris').

    Returns:
        A string with the formatted address and latitude/longitude coordinates.
    """
    try:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
        if not api_key:
            return "Error: GOOGLE_MAPS_API_KEY environment variable is not set."

        geo_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={api_key}"
        req = urllib.request.Request(geo_url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        if data.get("status") != "OK" or not data.get("results"):
            return f"Geocoding failed for '{address}': {data.get('status', 'No results')}"

        result = data["results"][0]
        formatted_address = result.get("formatted_address", address)
        location = result.get("geometry", {}).get("location", {})
        lat = location.get("lat")
        lng = location.get("lng")
        return f"Address: {formatted_address}\nLocation: Latitude {lat}, Longitude {lng}"
    except Exception as e:
        return f"Geocoding error for '{address}': {str(e)}"


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "tourist_attraction",
    radius_meters: float = 3000.0,
) -> str:
    """Finds nearby places of a given type around a coordinate using Google Places API (New).

    Args:
        latitude: Latitude of the center location.
        longitude: Longitude of the center location.
        place_type: Type of place to search for (e.g. 'tourist_attraction', 'restaurant', 'cafe', 'museum', 'park').
        radius_meters: Radius in meters around the location (default 3000m).

    Returns:
        A formatted list of nearby places including name, address, location coordinates, and rating.
    """
    try:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
        if not api_key:
            return "Error: GOOGLE_MAPS_API_KEY environment variable is not set."

        url = "https://places.googleapis.com/v1/places:searchNearby"
        payload = {
            "includedTypes": [place_type],
            "maxResultCount": 5,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": latitude, "longitude": longitude},
                    "radius": float(radius_meters),
                }
            },
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.rating",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        places = data.get("places", [])
        if not places:
            return f"No nearby places of type '{place_type}' found within {radius_meters}m."

        formatted = []
        for p in places:
            name = p.get("displayName", {}).get("text", "Unknown")
            addr = p.get("formattedAddress", "No address")
            loc = p.get("location", {})
            rating = p.get("rating", "N/A")
            formatted.append(
                f"- Name: {name}\n"
                f"  Address: {addr}\n"
                f"  Location: Latitude {loc.get('latitude')}, Longitude {loc.get('longitude')}\n"
                f"  Rating: {rating}"
            )
        return f"Nearby '{place_type}' locations:\n\n" + "\n\n".join(formatted)
    except Exception as e:
        return f"Places API error: {str(e)}"


def generate_destination_image(prompt: str, tool_context: ToolContext) -> str:
    """Generates an image for a travel destination, landmark, or scenic item using gemini-3.1-flash-lite-image model in global region.

    Saves the image as a session artifact and uploads it directly to Google Cloud Storage.

    Args:
        prompt: Detailed description of the travel destination or landmark scene to generate.

    Returns:
        The public HTTPS URL of the uploaded image in Google Cloud Storage.
    """
    try:
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
        )

        if not response.candidates or not response.candidates[0].content.parts:
            return "Failed to generate image: empty response from model."

        part = response.candidates[0].content.parts[0]
        if not part.inline_data or not part.inline_data.data:
            return "Failed to generate image: no image data returned from model."

        image_bytes = part.inline_data.data
        mime_type = part.inline_data.mime_type or "image/jpeg"
        ext = "png" if "png" in mime_type else "jpg"

        filename = f"destination_{uuid.uuid4().hex[:8]}.{ext}"

        # 1. Save artifact for Playground Artifacts panel
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload image bytes to public GCS bucket (without writing to disk)
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return f"Successfully generated destination image. Public URL: {public_url}"
    except Exception as e:
        return f"Image generation error: {str(e)}"


def generate_destination_video(prompt: str, tool_context: ToolContext) -> str:
    """Generates a short video for a travel destination, landmark, or scenic item using gemini-omni-flash-preview model in global region.

    Saves the video as a session artifact and uploads it directly to Google Cloud Storage.

    Args:
        prompt: Detailed description of the travel destination or scenic video scene to generate.

    Returns:
        The public HTTPS URL of the uploaded video in Google Cloud Storage.
    """
    try:
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )
        response = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
        )

        video_bytes = None
        mime_type = "video/mp4"

        if getattr(response, "output_video", None) and getattr(response.output_video, "bytes_b64_data", None):
            video_bytes = base64.b64decode(response.output_video.bytes_b64_data)
            mime_type = getattr(response.output_video, "mime_type", None) or "video/mp4"
        elif getattr(response, "outputs", None):
            for out in response.outputs:
                if getattr(out, "bytes_b64_data", None):
                    video_bytes = base64.b64decode(out.bytes_b64_data)
                    if getattr(out, "mime_type", None):
                        mime_type = out.mime_type
                    break

        if not video_bytes:
            return "Failed to generate video: no video bytes returned from model."

        ext = "mp4"
        filename = f"destination_video_{uuid.uuid4().hex[:8]}.{ext}"

        # 1. Save artifact for Playground Artifacts panel
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload video bytes to public GCS bucket (without writing to disk)
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return f"Successfully generated destination video. Public URL: {public_url}"
    except Exception as e:
        return f"Video generation error: {str(e)}"


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are an expert Travel Concierge Agent. "
        "You can search travel destinations from Firestore, view destination details, add new destinations to the catalog, "
        "fetch live real-time weather worldwide, convert travel budget currencies using live exchange rates, "
        "geocode addresses into coordinates, search nearby places (attractions, restaurants, parks, etc.) using Google Maps APIs, "
        "generate visual destination preview images and short travel video clips saved as artifacts and uploaded to Cloud Storage, "
        "execute Python code safely in a sandbox environment, "
        "and check current time for travel planning. "
        "CRITICAL: Always remember and strictly adhere to all user allergies (e.g., food, nuts, shellfish, gluten, environmental, medical) and dietary restrictions disclosed across past or current sessions. "
        "Proactively check stored user memories for allergies before recommending restaurants, destinations, activities, or itineraries."
    ),
    workflow_description="Analyze the user request, call appropriate tools, and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=get_code_executor(),
    tools=[
        PreloadMemoryTool(),
        list_destinations,
        get_destination,
        add_destination,
        get_live_weather,
        convert_currency,
        geocode_address,
        find_nearby_places,
        generate_destination_image,
        generate_destination_video,
        get_current_time,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)




app = App(
    root_agent=root_agent,
    name="app",
)





