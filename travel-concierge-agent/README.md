# Travel Concierge AI Agent

A conversational AI travel concierge built with the **Google Agent Development Kit (ADK)**, deployed to **Google Cloud Agent Engine / Cloud Run**, and featuring rich multi-tool integration, Memory Bank session persistence, and A2UI structured user interfaces.

---

## 🌟 What the Agent Does

The Travel Concierge Agent helps travelers discover destination recommendations, check real-time weather worldwide, convert travel budget currencies, search nearby places via Google Maps, generate visual destination previews (images and videos), and remember personal travel preferences across sessions.

---

## 🛠️ Integrated Tools & Capabilities

Based on the codebase in `app/agent.py`:

- **Firestore Destination Catalog**:
  - `list_destinations(category)`: Queries destinations in Google Cloud Firestore by category (e.g. *Beach & Relaxation*, *Culture & Heritage*).
  - `get_destination(destination_id)`: Retrieves complete destination details from Firestore.
  - `add_destination(...)`: Adds new travel destinations to the Firestore catalog.
- **Memory Bank & Preferences**:
  - `PreloadMemoryTool` & `generate_memories_callback`: Automatically pre-loads and updates user travel styles, budget tiers, and allergies across past and current sessions using Vertex AI Memory Service.
- **Live Weather Forecasts**:
  - `get_live_weather(location)`: Fetches real-time weather conditions worldwide via the Open-Meteo REST API.
- **Currency Conversion**:
  - `convert_currency(amount, from_currency, to_currency)`: Performs real-time exchange rate calculations using the Frankfurter API.
- **Google Maps Integration**:
  - `geocode_address(address)`: Converts addresses and landmark names into latitude/longitude coordinates via Google Maps Geocoding API.
  - `find_nearby_places(location, place_type, radius)`: Finds nearby attractions, restaurants, and parks using Google Maps Places API.
- **Vertex AI Image & Video Generation**:
  - `generate_destination_image(prompt)`: Generates scenic destination previews using Vertex AI `gemini-3.1-flash-lite-image`.
  - `generate_destination_video(prompt)`: Generates short destination video clips using Google's Omni model (`gemini-omni-flash-preview`) in the `global` region.
- **Google Cloud Storage (GCS)**:
  - Uploads generated image and video bytes directly to a public Cloud Storage bucket (`travel-concierge-assets-...`) and returns public HTTPS URLs.
  - Saves generated media as session artifacts via ADK `ToolContext`.
- **A2UI (Agent-to-User Interface)**:
  - Generates structured, responsive card layouts (`Card`, `Column`, `Row`, `Text`, `Image`) rendered directly in the user interface.
- **Python Code Execution Sandbox**:
  - `get_code_executor()`: Runs sandboxed Python code for travel budget splitting and math calculations.

---

## ☁️ Google Cloud Services & Architecture

- **Google Cloud Agent Engine (Agent Runtime)**: Managed agent execution runtime hosting the ADK root agent (`us-east1`).
- **Vertex AI**: Powers agent reasoning (`gemini-2.5-flash`), memory services, and multimodal generation (`gemini-3.1-flash-lite-image` and `gemini-omni-flash-preview`).
- **Google Cloud Firestore**: NoSQL document database hosting the travel catalog.
- **Google Cloud Storage (GCS)**: Public asset storage bucket for generated destination images and videos.
- **Google Cloud Run**: Serverless container platform hosting the FastAPI web frontend proxy (`us-central1`).
- **Google Maps Platform**: Geocoding and Places APIs for location search.

---

## 📋 Implementation Status

| Feature / Capability | Status | Implementation Details |
|---|---|---|
| Firestore Catalog Search | ✅ Implemented | `list_destinations`, `get_destination`, `add_destination` |
| Long-term Session Memory | ✅ Implemented | `PreloadMemoryTool` & ADK memory callbacks |
| Live Weather & Currency Tools | ✅ Implemented | Open-Meteo & Frankfurter APIs |
| Google Maps Places & Geocoding | ✅ Implemented | Google Maps Platform APIs |
| Visual Image Generation | ✅ Implemented | `gemini-3.1-flash-lite-image` + GCS upload |
| Visual Video Generation | ✅ Implemented | `gemini-omni-flash-preview` + GCS upload |
| Structured A2UI Components | ✅ Implemented | `A2uiSchemaManager` v0.8 callbacks |
| Python Code Sandbox | ✅ Implemented | ADK built-in code executor |
| Dedicated Itinerary Builder Table | ⏳ Planned | *Planned, not yet implemented as a separate database tool* |
| Cloud Trace Telemetry | ⏳ Planned | *Planned, not yet enabled in default setup* |

---

## 🚀 Setup & Local Execution Instructions

### Prerequisites

- Python 3.11+
- `uv` package manager (`pip install uv`)
- Google Cloud SDK (`gcloud` CLI authenticated with GCP project)

### 1. Install Dependencies

```bash
uv sync
```

### 2. Run Agent via CLI

To run a prompt against the agent locally using the command line:

```bash
agents-cli run "List all Beach & Relaxation destinations from our travel catalog."
```

### 3. Start Local Agent Playground

To interact with the agent using the web-based playground:

```bash
agents-cli playground
```

### 4. Run Web Frontend Locally

Navigate to the `frontend/` directory, set the required environment variables, and start the FastAPI server:

```bash
cd frontend
pip install -r requirements.txt

export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_NUMBER>/locations/<LOCATION>/reasoningEngines/<ENGINE_ID>"
export AGENT_DIRECTORY="app"

python main.py
```

Open a browser and navigate to port 8080 on localhost to interact with the plain chat UI.
