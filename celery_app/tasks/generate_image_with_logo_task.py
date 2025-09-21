"""
Text-to-image generation task with logo overlay using Qwen image on Replicate.
Generates an image from a prompt, overlays a logo in the bottom-left corner,
ensures 1:1 aspect ratio, and saves as an asset.
"""

import os
import uuid
import requests
from io import BytesIO
from PIL import Image, ImageOps
import replicate
from celery_app.celery_app import celery_app
from celery_app.streamer import get_task_streamer
from celery_app.tasks.database import get_db_context
from models.asset import Asset
from google.cloud import storage
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Logo configuration
LOGO_URL = "https://storage.googleapis.com/woopdi-cloud-assets/woopdi-light-background-dark-logo.png"
LOGO_POSITION = "bottom_left"  # bottom_left, bottom_right, top_left, top_right
LOGO_SIZE_PERCENT = 0.15  # Logo size as percentage of image width
TARGET_SIZE = (1024, 1024)  # 1:1 aspect ratio target size

@celery_app.task(bind=True, name='celery_app.tasks.generate_image_with_logo_task')
def generate_image_with_logo_task(
    self,
    prompt: str,
    user_id: int = None,
    guidance: float = 4.0,
    num_inference_steps: int = 50
) -> dict:
    """
    Generate an image from text prompt, overlay logo, and save as asset.

    Args:
        prompt: Text prompt for image generation
        user_id: User ID for asset ownership
        guidance: Guidance scale for image generation (default: 4.0)
        num_inference_steps: Number of inference steps (default: 50)

    Returns:
        dict: Asset details including ID, URL, and metadata
    """
    # Get the task streamer for progress updates
    streamer = get_task_streamer(self)

    try:
        # Initial update
        streamer.update("Starting image generation task", type="task_start")

        # Step 1: Generate image with Qwen
        streamer.update("Generating image with Qwen AI...", type="progress")
        logger.info(f"Generating image for prompt: {prompt}")

        # Generate a random seed for unique image generation
        import random
        random_seed = random.randint(0, 1000000)

        input_params = {
            "prompt": prompt,
            "guidance": guidance,
            "num_inference_steps": num_inference_steps,
            "aspect_ratio": "1:1",  # Use Qwen's built-in aspect ratio
            "seed": random_seed  # Add random seed for unique generation
        }

        output = replicate.run(
            "qwen/qwen-image",
            input=input_params
        )

        # Debug logging to understand output format
        logger.info(f"Replicate output type: {type(output)}")
        logger.info(f"Replicate output content: {output}")
        if isinstance(output, list) and len(output) > 0:
            logger.info(f"First output item type: {type(output[0])}")
            logger.info(f"First output item content: {output[0]}")

        # Get the first image URL
        # Handle different output formats from Replicate
        if isinstance(output, list) and len(output) > 0:
            first_item = output[0]
            if hasattr(first_item, 'url') and callable(getattr(first_item, 'url')):
                image_url = first_item.url()
                logger.info(f"Using object.url() method: {image_url}")
            else:
                image_url = str(first_item)
                logger.info(f"Using direct string conversion: {image_url}")
        else:
            raise ValueError(f"Unexpected output format from Replicate: {output}")

        streamer.update("Image generated successfully, downloading...", type="progress")

        # Step 2: Download generated image
        response = requests.get(image_url)
        response.raise_for_status()
        generated_image = Image.open(BytesIO(response.content))

        # Step 3: Download and process logo
        streamer.update("Downloading and processing logo...", type="progress")
        logo_response = requests.get(LOGO_URL)
        logo_response.raise_for_status()
        logo = Image.open(BytesIO(logo_response.content))

        # Step 4: Process images
        streamer.update("Processing images and overlaying logo...", type="progress")

        # Resize logo based on percentage of image width
        logo_width = int(generated_image.width * LOGO_SIZE_PERCENT)
        logo_height = int(logo.height * (logo_width / logo.width))
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

        # Resize to target dimensions (Qwen should already provide 1:1, but ensure it)
        final_image = generated_image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)

        # Overlay logo in bottom-left corner
        final_image = _overlay_logo(final_image, logo, LOGO_POSITION)

        # Step 5: Upload to Google Cloud Storage
        streamer.update("Uploading to cloud storage...", type="progress")

        # Generate unique filename
        filename = f"generated_{uuid.uuid4().hex}.png"
        bucket_name = os.getenv("GCP_BUCKET_NAME")
        blob_name = f"generated-images/{filename}"

        # Upload to GCP
        public_url = _upload_to_gcp(final_image, blob_name, bucket_name)

        # Step 6: Save to database
        streamer.update("Saving asset to database...", type="progress")

        asset_id = None
        with get_db_context() as db:
            asset = Asset(
                filename=filename,
                bucket_name=bucket_name,
                file_path=blob_name,
                content_type="image/png",
                file_size=len(_image_to_bytes(final_image)),
                user_id=user_id,
                preserve=False,
                public_url=public_url,
                upload_source="ai_generation",
                meta={
                    "prompt": prompt,
                    "guidance": guidance,
                    "num_inference_steps": num_inference_steps,
                    "ai_model": "qwen-image",
                    "logo_overlay": True,
                    "logo_position": LOGO_POSITION,
                    "aspect_ratio": "1:1",
                    "target_size": f"{TARGET_SIZE[0]}x{TARGET_SIZE[1]}"
                }
            )

            db.add(asset)
            db.commit()
            db.refresh(asset)
            asset_id = asset.id  # Get the ID while session is still active

        # Send final result via WebSocket
        final_result = {
            "status": "completed",
            "asset_id": asset_id,
            "public_url": public_url,
            "filename": filename,
            "message": "Image generated and saved successfully"
        }

        streamer.update("Image generation completed successfully!", type="task_end", data=final_result)

        return final_result

    except Exception as e:
        error_message = f"Task failed with error: {str(e)}"
        logger.error(error_message, exc_info=True)
        streamer.update(error_message, type="task_error")
        return {
            "status": "failed",
            "error": str(e)
        }

def _overlay_logo(base_image: Image.Image, logo: Image.Image, position: str) -> Image.Image:
    """Overlay logo on base image at specified position."""
    base_width, base_height = base_image.size

    if position == "bottom_left":
        x = 20  # Small margin from edge
        y = base_height - logo.height - 20
    elif position == "bottom_right":
        x = base_width - logo.width - 20
        y = base_height - logo.height - 20
    elif position == "top_left":
        x = 20
        y = 20
    elif position == "top_right":
        x = base_width - logo.width - 20
        y = 20
    else:
        # Default to bottom_left
        x = 20
        y = base_height - logo.height - 20

    # Create a copy of the base image
    result = base_image.copy()

    # Add semi-transparent background to logo for better visibility
    logo_with_bg = Image.new('RGBA', logo.size, (255, 255, 255, 180))
    logo_with_bg.paste(logo, (0, 0), logo)

    # Overlay the logo
    result.paste(logo_with_bg, (x, y), logo_with_bg)

    return result

def _upload_to_gcp(image: Image.Image, blob_name: str, bucket_name: str) -> str:
    """Upload image to Google Cloud Storage and return public URL."""
    try:
        # Initialize GCP client
        service_account_key = os.getenv("GCP_SERVICE_ACCOUNT_KEY")
        if not service_account_key:
            raise ValueError("GCP_SERVICE_ACCOUNT_KEY environment variable not set")

        client = storage.Client.from_service_account_json(service_account_key)
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)

        # Convert image to bytes
        image_bytes = _image_to_bytes(image)

        # Upload the image
        blob.upload_from_string(image_bytes, content_type="image/png")

        # Return public URL
        return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"

    except Exception as e:
        logger.error(f"GCP upload failed: {str(e)}")
        raise

def _image_to_bytes(image: Image.Image) -> bytes:
    """Convert PIL Image to bytes."""
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
