import io
import os
import urllib.request
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Canvas Setup
WIDTH, HEIGHT = 1280, 720
FPS = 30

# Colors (RGB)
BG_COLOR = (15, 23, 42)          # #0f172a
PANEL_BG = (30, 41, 59)          # #1e293b
PANEL_BORDER = (51, 65, 85)      # #334155
ACCENT_BLUE = (2, 132, 199)      # #0284c7
USER_BUBBLE = (3, 105, 161)      # #0369a1
AGENT_BUBBLE = (30, 41, 59)     # #1e293b
TOOL_BADGE_BG = (12, 74, 110)    # #0c4a6e
TOOL_BADGE_TXT = (56, 189, 248)  # #38bdf8
TEXT_WHITE = (248, 250, 252)     # #f8fafc
TEXT_MUTED = (148, 163, 184)     # #94a3b8
GREEN_DOT = (34, 197, 94)        # #22c55e

# Load Fonts
FONT_TITLE = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 22)
FONT_SUBTITLE = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 14)
FONT_BODY = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 16)
FONT_BODY_BOLD = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 16)
FONT_CODE = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf", 14)

# Fetch Generated Image for Scene 2
IMAGE_URL = "https://storage.googleapis.com/travel-concierge-assets-qwiklabs-gcp-01-19d6c0b95c76/destination_fcb45153.jpg"
req = urllib.request.Request(IMAGE_URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as resp:
    generated_img_data = resp.read()

gen_img_pil = Image.open(io.BytesIO(generated_img_data)).convert("RGB")
gen_img_pil = gen_img_pil.resize((360, 200), Image.Resampling.LANCZOS)

def draw_window_frame(draw):
    # Main window box
    draw.rounded_rectangle([40, 30, WIDTH - 40, HEIGHT - 30], radius=16, fill=PANEL_BG, outline=PANEL_BORDER, width=2)
    # Header bar
    draw.rounded_rectangle([40, 30, WIDTH - 40, 85], radius=16, fill=(15, 23, 42))
    draw.rectangle([40, 70, WIDTH - 40, 85], fill=(15, 23, 42))
    draw.line([40, 85, WIDTH - 40, 85], fill=PANEL_BORDER, width=1)
    
    # Window Dots
    draw.ellipse([60, 52, 72, 64], fill=(239, 68, 68))
    draw.ellipse([80, 52, 92, 64], fill=(245, 158, 11))
    draw.ellipse([100, 52, 112, 64], fill=(34, 197, 94))
    
    # Header Title & Status
    draw.text((130, 47), "Travel Concierge AI Agent", font=FONT_TITLE, fill=TEXT_WHITE)
    draw.text((420, 53), "• Online (Google Agent Runtime & A2UI)", font=FONT_SUBTITLE, fill=GREEN_DOT)

def create_frame(scene_type, progress):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Background Glow
    draw.ellipse([WIDTH // 2 - 400, -200, WIDTH // 2 + 400, 400], fill=(2, 44, 80))
    
    draw_window_frame(draw)
    
    chat_y = 110
    
    if scene_type == 0:
        # Title Intro Screen
        draw.text((WIDTH // 2 - 240, HEIGHT // 2 - 60), "🧳 Travel Concierge AI Agent", font=ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 36), fill=TEXT_WHITE)
        draw.text((WIDTH // 2 - 280, HEIGHT // 2 + 10), "Demonstrating Firestore Catalog Search, Multi-Tool Execution & Image Generation", font=FONT_SUBTITLE, fill=TEXT_MUTED)
        draw.rounded_rectangle([WIDTH // 2 - 140, HEIGHT // 2 + 60, WIDTH // 2 + 140, HEIGHT // 2 + 95], radius=20, fill=ACCENT_BLUE)
        draw.text((WIDTH // 2 - 110, HEIGHT // 2 + 68), "Build with Gemini Demo", font=FONT_BODY_BOLD, fill=TEXT_WHITE)

    elif scene_type == 1:
        # Scene 1: Database Lookup / Catalog Search
        # User Prompt 1 (Typewriter effect)
        full_text_1 = "List all Beach & Relaxation destinations in our travel catalog."
        chars_1 = int(len(full_text_1) * min(progress * 2, 1.0))
        text_1 = full_text_1[:chars_1]
        
        # User Bubble
        draw.rounded_rectangle([WIDTH - 540, chat_y, WIDTH - 70, chat_y + 45], radius=12, fill=USER_BUBBLE)
        draw.text((WIDTH - 520, chat_y + 12), text_1, font=FONT_BODY, fill=TEXT_WHITE)
        
        if progress > 0.4:
            # Tool Call Badge
            tool_y = chat_y + 60
            draw.rounded_rectangle([70, tool_y, 490, tool_y + 32], radius=8, fill=TOOL_BADGE_BG, outline=TOOL_BADGE_TXT, width=1)
            draw.text((85, tool_y + 6), "⚡ tool_call: list_destinations(category='Beach & Relaxation')", font=FONT_CODE, fill=TOOL_BADGE_TXT)
            
        if progress > 0.65:
            # Agent Response
            resp_y = chat_y + 105
            draw.rounded_rectangle([70, resp_y, 760, resp_y + 210], radius=12, fill=AGENT_BUBBLE, outline=PANEL_BORDER, width=1)
            
            draw.text((90, resp_y + 15), "🧳 Agent Response (Firestore Catalog Lookup):", font=FONT_BODY_BOLD, fill=TEXT_WHITE)
            draw.text((90, resp_y + 45), "Found matching destinations in the 'Beach & Relaxation' category:", font=FONT_BODY, fill=TEXT_MUTED)
            
            # Card element
            draw.rounded_rectangle([90, resp_y + 75, 740, resp_y + 190], radius=8, fill=(15, 23, 42), outline=ACCENT_BLUE, width=1)
            draw.text((110, resp_y + 88), "📍 Santorini (Greece) — Budget: $$$$", font=FONT_BODY_BOLD, fill=TEXT_WHITE)
            draw.text((110, resp_y + 115), "Description: Famous Cycladic island with whitewashed cliffside villages,", font=FONT_BODY, fill=TEXT_MUTED)
            draw.text((110, resp_y + 138), "stunning sunsets over the Aegean sea, and volcanic beaches.", font=FONT_BODY, fill=TEXT_MUTED)
            draw.text((110, resp_y + 162), "🗓️ Best Time to Visit: May to October", font=FONT_BODY, fill=TOOL_BADGE_TXT)

    elif scene_type == 2:
        # Scene 2: Multi-Tool Execution & Image Generation
        # Show prompt 1 collapsed at top
        draw.rounded_rectangle([WIDTH - 440, chat_y, WIDTH - 70, chat_y + 35], radius=10, fill=(30, 41, 59))
        draw.text((WIDTH - 420, chat_y + 8), "List all Beach & Relaxation destinations...", font=FONT_SUBTITLE, fill=TEXT_MUTED)
        
        chat_y += 50
        
        # User Prompt 2 (Typewriter effect)
        full_text_2 = "Check live weather in Santorini, convert $200 USD to EUR, and generate a destination preview."
        chars_2 = int(len(full_text_2) * min(progress * 2.5, 1.0))
        text_2 = full_text_2[:chars_2]
        
        draw.rounded_rectangle([WIDTH - 760, chat_y, WIDTH - 70, chat_y + 45], radius=12, fill=USER_BUBBLE)
        draw.text((WIDTH - 740, chat_y + 12), text_2, font=FONT_BODY, fill=TEXT_WHITE)
        
        if progress > 0.3:
            # Tool Badges Stack
            tb1_y = chat_y + 55
            draw.rounded_rectangle([70, tb1_y, 450, tb1_y + 26], radius=6, fill=TOOL_BADGE_BG, outline=TOOL_BADGE_TXT, width=1)
            draw.text((80, tb1_y + 4), "🌤️ tool_call: get_live_weather(location='Santorini')", font=FONT_CODE, fill=TOOL_BADGE_TXT)
            
            tb2_y = tb1_y + 32
            draw.rounded_rectangle([70, tb2_y, 500, tb2_y + 26], radius=6, fill=TOOL_BADGE_BG, outline=TOOL_BADGE_TXT, width=1)
            draw.text((80, tb2_y + 4), "💱 tool_call: convert_currency(amount=200, USD -> EUR)", font=FONT_CODE, fill=TOOL_BADGE_TXT)
            
            tb3_y = tb2_y + 32
            draw.rounded_rectangle([70, tb3_y, 530, tb3_y + 26], radius=6, fill=TOOL_BADGE_BG, outline=TOOL_BADGE_TXT, width=1)
            draw.text((80, tb3_y + 4), "🎨 tool_call: generate_destination_image(prompt='Santorini')", font=FONT_CODE, fill=TOOL_BADGE_TXT)

        if progress > 0.55:
            # Agent Multi-tool Response with Generated Image Card
            resp_y = chat_y + 155
            draw.rounded_rectangle([70, resp_y, 820, resp_y + 260], radius=12, fill=AGENT_BUBBLE, outline=PANEL_BORDER, width=1)
            
            # Left Column: Weather & Currency
            draw.text((90, resp_y + 15), "🧳 Agent Response & Live Travel Data:", font=FONT_BODY_BOLD, fill=TEXT_WHITE)
            draw.text((90, resp_y + 45), "🌤️ Live Weather: 22.3°C (72.1°F), Wind 31.9 km/h", font=FONT_BODY, fill=TEXT_WHITE)
            draw.text((90, resp_y + 75), "💱 Currency Exchange: $200.00 USD = €175.39 EUR", font=FONT_BODY, fill=TEXT_WHITE)
            draw.text((90, resp_y + 98), "   (Rate: 1 USD = 0.8769 EUR via ECB)", font=FONT_SUBTITLE, fill=TEXT_MUTED)
            draw.text((90, resp_y + 130), "☁️ Cloud Storage Asset:", font=FONT_BODY_BOLD, fill=TEXT_WHITE)
            draw.text((90, resp_y + 155), "Uploaded to public GCS bucket", font=FONT_SUBTITLE, fill=TOOL_BADGE_TXT)
            draw.text((90, resp_y + 175), "travel-concierge-assets-...", font=FONT_CODE, fill=TEXT_MUTED)

            # Right Column: Generated Image Preview Card
            img_x, img_y = 430, resp_y + 40
            draw.rounded_rectangle([img_x - 5, img_y - 5, img_x + 365, img_y + 205], radius=10, fill=(15, 23, 42), outline=ACCENT_BLUE, width=2)
            img.paste(gen_img_pil, (img_x, img_y))

    elif scene_type == 3:
        # Outro Screen
        draw.text((WIDTH // 2 - 210, HEIGHT // 2 - 60), "🎉 Travel Concierge AI Agent", font=ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 32), fill=TEXT_WHITE)
        draw.text((WIDTH // 2 - 250, HEIGHT // 2 + 10), "Successfully verified end-to-end agent capabilities on Google Cloud!", font=FONT_BODY, fill=GREEN_DOT)
        draw.text((WIDTH // 2 - 200, HEIGHT // 2 + 50), "• Firestore Catalog Lookup • Live Weather & Currency", font=FONT_SUBTITLE, fill=TEXT_MUTED)
        draw.text((WIDTH // 2 - 200, HEIGHT // 2 + 75), "• Gemini Image & Video Generation • Cloud Storage Upload", font=FONT_SUBTITLE, fill=TEXT_MUTED)

    return np.array(img)

def main():
    video_filename = "demo_video.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(video_filename, fourcc, FPS, (WIDTH, HEIGHT))

    print("Rendering Demo Video...")

    # Scene 0: Title Card (3 seconds = 90 frames)
    for f in range(90):
        frame = create_frame(0, f / 90.0)
        out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    # Scene 1: Catalog Search & Database Lookup (7 seconds = 210 frames)
    for f in range(210):
        frame = create_frame(1, f / 210.0)
        out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    # Scene 2: Multi-Tool Execution & Image Generation (10 seconds = 300 frames)
    for f in range(300):
        frame = create_frame(2, f / 300.0)
        out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    # Scene 3: Outro Card (3 seconds = 90 frames)
    for f in range(90):
        frame = create_frame(3, f / 90.0)
        out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    out.release()
    print(f"Successfully rendered demo video to {video_filename}!")

if __name__ == "__main__":
    main()
