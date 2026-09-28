"""Seed Firestore with initial destinations collection."""
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-19d6c0b95c76"

DESTINATIONS = [
    {
        "id": "kyoto-japan",
        "name": "Kyoto",
        "country": "Japan",
        "category": "Culture & Heritage",
        "budget_tier": "$$$",
        "description": "Japan's cultural capital known for classical Buddhist temples, gardens, imperial palaces, and traditional wooden houses.",
        "top_activities": [
            "Visit Fushimi Inari Shrine",
            "Stroll through Arashiyama Bamboo Grove",
            "Experience a traditional Tea Ceremony in Gion",
        ],
        "best_time_to_visit": "Spring (Cherry Blossoms) & Autumn (Foliage)",
    },
    {
        "id": "santorini-greece",
        "name": "Santorini",
        "country": "Greece",
        "category": "Beach & Relaxation",
        "budget_tier": "$$$$",
        "description": "Famous Cycladic island with whitewashed cliffside villages, stunning sunsets over the Aegean sea, and volcanic beaches.",
        "top_activities": [
            "Watch Oia Sunset",
            "Catamaran Cruise in the Caldera",
            "Wine tasting at cliffside vineyards",
        ],
        "best_time_to_visit": "May to October",
    },
    {
        "id": "banff-canada",
        "name": "Banff National Park",
        "country": "Canada",
        "category": "Mountain & Adventure",
        "budget_tier": "$$",
        "description": "Stunning Canadian Rockies destination with turquoise glacial lakes, alpine hikes, and abundant wildlife.",
        "top_activities": [
            "Canoeing on Lake Louise",
            "Hike to Lake Agnes Tea House",
            "Drive the scenic Icefields Parkway",
        ],
        "best_time_to_visit": "June to September for hiking; December to March for skiing",
    },
    {
        "id": "cappadocia-turkey",
        "name": "Cappadocia",
        "country": "Turkey",
        "category": "Culture & Adventure",
        "budget_tier": "$$",
        "description": "Unique landscape famed for fairy chimneys, cave hotels, underground cities, and hot air balloon rides at sunrise.",
        "top_activities": [
            "Hot Air Balloon Ride at Sunrise",
            "Explore Derinkuyu Underground City",
            "Stay in a traditional cave hotel",
        ],
        "best_time_to_visit": "April to June & September to October",
    },
    {
        "id": "reykjavik-iceland",
        "name": "Reykjavik & Golden Circle",
        "country": "Iceland",
        "category": "Nature & Wonders",
        "budget_tier": "$$$$",
        "description": "Gateway to Iceland's dramatic volcanic and icy landscapes, geysers, thermal lagoons, and Northern Lights.",
        "top_activities": [
            "Bathe in the geothermal Blue Lagoon",
            "Tour Golden Circle waterfalls and geysers",
            "Chase the Northern Lights",
        ],
        "best_time_to_visit": "September to March for Northern Lights; June to August for Midnight Sun",
    },
]


def seed_database():
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("destinations")
    print(f"Seeding Firestore collection 'destinations' in project '{PROJECT_ID}'...")

    for dest in DESTINATIONS:
        doc_ref = collection_ref.document(dest["id"])
        doc_ref.set(dest)
        print(f"  ✓ Added/Updated: {dest['name']} ({dest['id']})")

    print("Seeding completed successfully!")


if __name__ == "__main__":
    seed_database()
