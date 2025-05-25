# ai/microservice/text_generator.py
from .base_service import AIMicroService
from diffusers import DiffusionPipeline
from ai import *
import threading
import os

class TextToSpeechService(AIMicroService):
    def __init__(self):
        self.modelLoaded = False

    def loadModel(self):
        model_id = "Heartsync/NSFW-Uncensored"
        try:
            self.imager = DiffusionPipeline.from_pretrained(
                model_id
            ).to("cuda")
            PAIALogger().info(f"TextToImageService initialized with {model_id}")
            self.modelLoaded = True
        except Exception as e:
            PAIALogger().error(f"Failed to load model: {str(e)}")
            raise

    def process(self, query):
        if not self.modelLoaded:
            self.loadModel()

        prompt = query.get("text", "")
        height = int(query.get("height", 512))
        width = int(query.get("width", 512))
        guidance_scale = float(query.get("guidance_scale", 8.0))
        num_inference_steps = int(query.get("num_inference_steps", 20))
        negative_prompt = query.get("negative_prompt", "ugly, deformed, disfigured, poor quality, low resolution")
        PAIALogger().debug(f"Processing query: prompt='{prompt}', height={height}, width={width}, guidance_scale={guidance_scale}, num_inference_steps={num_inference_steps}, negative_prompt='{negative_prompt}'")

        if not prompt:
            PAIALogger().error("No prompt provided")
            yield {"error": "No prompt provided for image generation"}
            return

        try:
            safe_prompt = "".join(c for c in prompt if c.isalnum() or c in " _-").strip()[:50]
            if not safe_prompt:
                safe_prompt = "image"
            image_path = f"ui/image/{safe_prompt}_{threading.current_thread().name}.png"
            os.makedirs("ui/image", exist_ok=True)

            result = self.imager(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height
            )["images"][0]

            result.save(image_path)
            image_url = f"http://localhost:8080/image/{safe_prompt}_{threading.current_thread().name}.png"
            PAIALogger().info(f"Generated image: {image_url}")
            yield {"result": image_url, "type": "image"}

        except Exception as e:
            PAIALogger().error(f"Error in image generation: {str(e)}")
            yield {"error": f"Image generation failed: {str(e)}"}

        PAIALogger().debug("End thread")