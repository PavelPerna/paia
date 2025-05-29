# ai/microservice/text_generator.py
from .base_service import AIMicroService
from transformers import pipeline, AutoModel, AutoTokenizer
from ai import *
import io
import os
import torch

class TextToImageService(AIMicroService):
    def __init__(self):
        self.modelLoaded = False

    def loadModel(self):
        try:
            model_id = "gpt2"
            PAIALogger().info(f"Loading model : {model_id}")
            self.imager = pipeline(model=model_id,torch_dtype=torch.float16,trust_remote_code=True)
            PAIALogger().info(f"TextToImageService initialized with { model_id}")
            self.modelLoaded = True
        except Exception as e:
            PAIALogger().error(f"Failed to load model: {str(e)}")
            raise

    def process(self, query):
        if not self.modelLoaded:
            self.loadModel()
        prompt = query.get("text", "")
        height = int(query.get("height", 256))
        width = int(query.get("width", 256))
        output_path = query.get("output_path", "ui/image")
        guidance_scale = float(query.get("guidance_scale", 6.3))
        num_inference_steps = int(query.get("num_inference_steps", 10))
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
            image_path = f"{output_path}/{safe_prompt}.png"
            os.mkdir(f"{output_path}", exist_ok=True)

            result = self.imager(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,

            )["images"][0]
            buffer = io.BytesIO()
            result.save(buffer, format="PNG")
            image_url = f"http://localhost:8080/ui/image/{safe_prompt}.png"
            PAIALogger().getLogger().info(f"Generated image: {image_url}")
            PAIALogger().getLogger().debug(f"Generated image: {result}")
            yield {"result": image_url, "type": "image","image_path":image_path}

        except Exception as e:
            PAIALogger().getLogger().error(f"Error in image generation: {str(e)}")
            yield {"error": f"Image generation failed: {str(e)}"}

        PAIALogger().debug("End thread")