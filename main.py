import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from PIL import Image, ImageDraw, ImageFont
from rembg import remove
import io
import os
import uuid

# --- Configuration ---
app = FastAPI()
OUTPUT_DIR = "outputs"
STATIC_DIR = "static"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount a static directory to serve the generated images
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

# --- Helper Functions ---

def generate_ai_background(text_prompt: str, width: int, height: int) -> Image:
    """
    *** THIS IS THE AI GENERATION PART ***
    This is where you would call Stable Diffusion (e.g., Replicate, Stability.ai).
    For the hackathon, we'll start with a simple gradient as a placeholder.
    """
    print(f"Generating AI background with prompt: {text_prompt}")
    
    # --- HACKATHON PLACEHOLDER ---
    # Replace this with your actual GenAI API call
    img = Image.new('RGB', (width, height), color = 'red')
    d = ImageDraw.Draw(img)
    # A simple gradient to show it's "AI-generated"
    for i in range(height):
        r = int(255 * (i / height))
        g = 0
        b = int(100 * (1 - (i / height)))
        d.line([(0, i), (width, i)], fill=(r, g, b))
    # --- END PLACEHOLDER ---
    
    # A real call would look like this (using a library like 'replicate'):
    # output = replicate.run(
    #     "stability-ai/sdxl:...",
    #     input={"prompt": text_prompt, "width": width, "height": height}
    # )
    # img = Image.open(io.BytesIO(requests.get(output[0]).content))
    
    return img

# --- API Endpoint ---

@app.post("/api/generate_ad")
async def generate_ad(
    product_image: UploadFile = File(...),
    logo_image: UploadFile = File(...),
    ad_text: str = Form(...),
    rules_prompt: str = Form(...)  # e.g., "A festive red and green background"
):
    try:
        # 1. Read and process images
        product_bytes = await product_image.read()
        logo_bytes = await logo_image.read()
        
        # 2. AI Background Removal (Feature 1)
        # Use 'rembg' to remove the background from the product
        product_no_bg_bytes = remove(product_bytes)
        product_clean = Image.open(io.BytesIO(product_no_bg_bytes)).convert("RGBA")
        
        logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
        
        # Define standard ad size
        AD_WIDTH, AD_HEIGHT = 1080, 1080
        
        # 3. AI Background Generation (Feature 1)
        # The "Manager" AI's prompt is passed to the "Worker" AI
        ai_background = generate_ai_background(rules_prompt, AD_WIDTH, AD_HEIGHT)
        
        # 4. Hybrid Composition (The "Professional Trick")
        # We use Pillow to assemble the ad. This is our "Hybrid Engine".
        final_ad = ai_background.copy().convert("RGBA")
        
        # --- Paste Product ---
        product_clean.thumbnail((AD_WIDTH * 0.6, AD_HEIGHT * 0.6)) # Resize
        product_pos = (
            (AD_WIDTH - product_clean.width) // 2, 
            (AD_HEIGHT - product_clean.height) // 2 + 50 # Center-ish
        )
        final_ad.paste(product_clean, product_pos, product_clean) # Paste with transparency
        
        # --- Paste Logo ---
        logo.thumbnail((AD_WIDTH * 0.2, AD_HEIGHT * 0.2)) # Resize
        logo_pos = (AD_WIDTH - logo.width - 50, AD_HEIGHT - logo.height - 50) # Bottom-right
        final_ad.paste(logo, logo_pos, logo) # Paste with transparency
        
        # --- Add Text ---
        draw = ImageDraw.Draw(final_ad)
        # You'd load a custom font (from Brand Kit) here. We'll use default.
        # font = ImageFont.truetype("my_font.ttf", 90)
        try:
            # Try to load a good default font
            font = ImageFont.truetype("Arial.ttf", 90)
        except IOError:
            font = ImageFont.load_default()
            
        text_bbox = draw.textbbox((0, 0), ad_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_pos = ((AD_WIDTH - text_width) // 2, 100) # Top-center
        draw.text(text_pos, ad_text, font=font, fill=(255, 255, 255))

        # 5. Save and return
        filename = f"{uuid.uuid4()}.png"
        output_path = os.path.join(OUTPUT_DIR, filename)
        final_ad.save(output_path, "PNG")
        
        # Return the URL where the frontend can find the image
        return {"success": True, "image_url": f"/outputs/{filename}"}

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("Visit http://127.0.0.1:8000 to see your app.")
    uvicorn.run(app, host="127.0.0.1", port=8000)
