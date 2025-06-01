# ai/service/translate.py
from transformers import pipeline
from paia import PAIALogger,PAIAService

logger = PAIALogger().getLogger()

class TranslateService(PAIAService):
    def __init__(self):
        self.translators = {}

    def process(self, query):
        text = query.get("text", "")
        source_language = query.get("source_language", "cs")
        target_language = query.get("target_language", "en")
        model_id = f"Helsinki-NLP/opus-mt-{source_language}-{target_language}"
        logger.debug(f"Processing query: text='{text}', source_language='{source_language}', target_language='{target_language}'")

        if not text:
            logger.error("No text provided")
            yield {"error": "No text provided for translation"}
            return

        try:
            if model_id not in self.translators:
                logger.info(f"Loading model: {model_id}")
                self.translators[model_id] = pipeline("translation", model=model_id)
            else:
                logger.debug(f"Using cached model: {model_id}")

            result = self.translators[model_id](text)[0]["translation_text"]
            logger.info(f"Translation result: {result}")
            yield {"result": result}

        except Exception as e:
            logger.error(f"Error in translation: {str(e)}")
            yield {"error": f"Translation failed: {str(e)}"}

        logger.debug("End thread")