# ai/service/text_generator.py
from transformers import pipeline
from paia import *
import os
from pathlib import Path
from gtts import gTTS

class TextToSpeechService(PAIAService):
    def __init__(self):
        self.modelLoaded = False

    def loadModel(self):
        pass

    def process(self, query):
        prompt = query.get("text", "")
        lang = query.get("lang", "cs")
        output_path = os.path.join(PAIAConfig().getUIDirectory(),"sound")
        output_addr = f"{PAIAConfig().getUIAddress()}/sound/"
        PAIALogger().debug(f"Processing query: prompt='{prompt}'")

        if not prompt:
            PAIALogger().error("No prompt provided")
            yield {"error": "No prompt provided for image generation"}
            return

        try:
            safe_prompt = "".join(c for c in prompt if c.isalnum() or c in " _-").strip()[:50]
            if not safe_prompt:
                safe_prompt = "sound"
                
            res_path = f"{output_path}/{safe_prompt}.mp3"
            res_addr = f"{output_addr}/{safe_prompt}.mp3"

            path = Path(output_path)
            path.mkdir(exist_ok=True,parents=True)

            result = gTTS(text=prompt, slow=False, lang=lang)
            result.save(res_path)
            
            PAIALogger().info(f"Generated sound: {res_addr}")
            yield {"result": res_addr, "type": "audio"}

        except Exception as e:
            PAIALogger().error(f"Error in image generation: {str(e)}")
            yield {"error": f"Image generation failed: {str(e)}"}

        PAIALogger().debug("End thread")