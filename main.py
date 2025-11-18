import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
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

# Mount static directories
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- Helper Functions ---

def generate_ai_background(text_prompt: str, width: int, height: int) -> Image:
    """
    *** THIS IS THE AI GENERATION PART ***
    This is a placeholder. Replace this with a real call to Stable Diffusion
    or another AI image API.
    """
    print(f"Generating AI background with prompt: {text_prompt}")
    
    # --- HACKATHON PLACEHOLDER ---
    # A simple gradient to show it's "AI-generated"
    img = Image.new('RGB', (width, height), color = 'red')
    d = ImageDraw.Draw(img)
    for i in range(height):
        r = int(255 * (i / height))
        g = 0
        b = int(100 * (1 - (i / height)))
        d.line([(0, i), (width, i)], fill=(r, g, b))
    
    return img

# --- Main Page Endpoint ---

@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    """
    Serves the main index.html file from the static folder.
    """
    try:
        with open(os.path.join(STATIC_DIR, "index.html")) as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Error: index.html not found</h1>", status_code=404)

# --- API Endpoint ---

@app.post("/api/generate_ad")
async def generate_ad(
    product_image: UploadFile = File(...),
    logo_image: UploadFile = File(...),
    ad_text: str = Form(...),
    rules_prompt: str = Form(...)
):
    try:
        # 1. Read and process images
        product_bytes = await product_image.read()
        logo_bytes = await logo_image.read()
        
        # 2. AI Background Removal
        product_no_bg_bytes = remove(product_bytes)
        product_clean = Image.open(io.BytesIO(product_no_bg_bytes)).convert("RGBA")
        
        logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
        
        # Define standard ad size
        AD_WIDTH, AD_HEIGHT = 1080, 1080
        
        # 3. AI Background Generation
        ai_background = generate_ai_background(rules_prompt, AD_WIDTH, AD_HEIGHT)
        
        # 4. Hybrid Composition (The "Professional Trick")
        final_ad = ai_background.copy().convert("RGBA")
        
        # --- Paste Product ---
        product_clean.thumbnail((AD_WIDTH * 0.6, AD_HEIGHT * 0.6))
        product_pos = (
            (AD_WIDTH - product_clean.width) // 2, 
            (AD_HEIGHT - product_clean.height) // 2 + 50
        )
        final_ad.paste(product_clean, product_pos, product_clean)
        
        # --- Paste Logo ---
        logo.thumbnail((AD_WIDTH * 0.2, AD_HEIGHT * 0.2))
        logo_pos = (AD_WIDTH - logo.width - 50, AD_HEIGHT - logo.height - 50)
        final_ad.paste(logo, logo_pos, logo)
        
        # --- Add Text ---
        draw = ImageDraw.Draw(final_ad)
        
        # *** FONT FIX ***
        # This is the safe, built-in font. It will always work.
        font_size = 90
        font = ImageFont.load_default(size=font_size)
        
        text_bbox = draw.textbbox((0, 0), ad_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_pos = ((AD_WIDTH - text_width) // 2, 100) # Top-center
        draw.text(text_pos, ad_text, font=font, fill=(255, 255, 255))

        # 5. Save and return
        filename = f"{uuid.uuid4()}.png"
        output_path = os.path.join(OUTPUT_DIR, filename)
        final_ad.save(output_path, "PNG")
        
        return {"success": True, "image_url": f"/outputs/{filename}"}

    except Exception as e:
        print(f"Error during ad generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # This is the "development" command.
    print("Starting server... Go to http://127.0.0.1:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
