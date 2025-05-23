# ai/microservice/text_generator.py
from .base_service import AIMicroService
from transformers import AutoModelForCausalLM, AutoTokenizer
from ai.logger import PAIALogger
import torch
import time
import threading

logger = PAIALogger().get()

class TextGenerationService(AIMicroService):
    def __init__(self):
        self.modelLoaded = False

    def loadModel(self):
        model_id = "gtp2"
        model_id = "Novaciano/NSFW-AMEBA-3.2-1B"
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id, trust_remote_code=True, torch_dtype=torch.bfloat16
            ).to("cuda")
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_id, trust_remote_code=True, torch_dtype=torch.bfloat16
            )

            self.tokenizer.pad_token = self.tokenizer.eos_token
            logger.info("TextGenerationService initialized")
            self.modelLoaded = True
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {str(e)}")
            raise

    def process(self, query):
        if not self.modelLoaded:
            self.loadModel()

        prompt = query.get("text", "")
        prefix = query.get("prefix", "")
        context = query.get("context", "")
        max_length = int(query.get("max_length", 50))
        logger.debug(f"Processing query: prompt='{prompt}', prefix='{prefix}', context='{context}', max_length={max_length}")

        if not prompt:
            logger.error("No prompt provided")
            yield {"error": "No prompt provided for text generation"}
            return

        try:
            full_prompt = f"{prefix} {prompt}".strip()
            logger.debug(f"Full prompt: {full_prompt}")
            input_ids = self.tokenizer.encode(full_prompt, return_tensors="pt").to(self.device)
            attention_mask = torch.ones(input_ids.shape, dtype=torch.long).to(self.device)

            generated_ids = input_ids
            self.model.eval()
            with torch.no_grad():
                for step in range(max_length - input_ids.shape[1]):
                    outputs = self.model(generated_ids, attention_mask=attention_mask)
                    next_token_logits = outputs.logits[:, -1, :]
                    next_token_id = torch.argmax(next_token_logits, dim=-1).unsqueeze(-1)
                    generated_ids = torch.cat((generated_ids, next_token_id), dim=1)
                    attention_mask = torch.cat((attention_mask, torch.ones((1, 1), dtype=torch.long).to(self.device)), dim=1)
                    
                    generated_text = self.tokenizer.decode(generated_ids[0], skip_special_tokens=True)
                    logger.debug(f"Generated text: {generated_text}")
                    yield {"result": generated_text}
                    time.sleep(0.2)

                    if next_token_id.item() == self.tokenizer.eos_token_id:
                        logger.info("EOS token reached")
                        break
        
        except Exception as e:
            logger.error(f"Error in text generation: {str(e)}")
            yield {"error": f"Text generation failed: {str(e)}"}

        logger.debug("End thread")