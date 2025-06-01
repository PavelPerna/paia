import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from datetime import datetime
from paia import PAIAService,PAIALogger

logger = PAIALogger()

class Chat(PAIAService):
    def __init__(self, model_id="Heartsync/NSFW-Uncensored"):
        """Initialize the chatbot with a specified model and conversation history."""
        self.model_id = model_id
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.history = []  # List to store conversation history
        self.max_history_length = 50  # Limit history to last 5 exchanges

    def load_model(self):
        if self.model:
            return
        """Load the pre-trained model and tokenizer."""
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id, 
                torch_dtype=torch.bfloat16 if self.device == "cuda" else torch.float32
            ).to(self.device)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.history_pipe = pipeline("summarization",model=self.model,tokenizer=self.tokenizer)
        except Exception as e:
            raise

    def add_to_history(self, user_input, response):
        self.load_model()
        """Add a user input and bot response to the conversation history."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history.append({"timestamp": timestamp, "user": user_input, "bot": response})
        # Keep only the last max_history_length exchanges
        if len(self.history) > self.max_history_length:
            self.history = self.history_pipe(self.get_history_context())[0]["summary"]

    def get_history_context(self):
        """Build a context string from the conversation history."""
        context = ""
        for entry in self.history:
            context += f"User: {entry['user']}\nBot: {entry['bot']}\n"
        return context

    def process(self,query):
        self.load_model()
        """Generate a response to the user input, incorporating history."""
        user_input = query.get("text","")
        max_length = int(query.get("max_length",50))
        max_tokens=max_length
        temperature=0.8

        if not user_input.strip():
            return "Please provide a valid input."
        
        try:
            # Build prompt with history and current input
            context = self.get_history_context()
            prompt = f"{context}User: {user_input}\nBot: "
            input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
            attention_mask = torch.ones(input_ids.shape, dtype=torch.long).to(self.device)

            # Generate response in streaming mode
            self.model.eval()
            generated_ids = input_ids
            generated_text = ""
            with torch.no_grad():
                for step in range(max_length + input_ids.shape[1]):
                    outputs = self.model(generated_ids,is_assistant=True, attention_mask=attention_mask, max_new_tokens=1 + input_ids.shape[1],stop_strings=["Bot","\n"],generate_full_text=False)
                    next_token_logits = outputs.logits[:, -1, :]
                    next_token_id = torch.argmax(next_token_logits, dim=-1).unsqueeze(-1)
                    generated_ids = torch.cat((generated_ids, next_token_id), dim=1)
                    attention_mask = torch.cat((attention_mask, torch.ones((1, 1), dtype=torch.long).to(self.device)), dim=1)

                    # Decode the new token
                    new_token = self.tokenizer.decode(next_token_id[0], skip_special_tokens=True)
                    if new_token in ["Bot","User"]:
                        break
                    if new_token:
                        generated_text += new_token
                        logger.debug(f"Streaming token: {new_token}")
                        yield {"result": generated_text}

                    # Stop if EOS token is reached
                    if next_token_id.item() == self.tokenizer.eos_token_id:
                        logger.info("EOS token reached")
                        break

            # Add final response to history
            self.add_to_history(user_input, generated_text)

        except Exception as e:
            logger.error(f"Error generating streaming response: {str(e)}")
            yield {"error": f"Streaming response failed: {str(e)}"}

    def display_history(self):
        """Display the conversation history."""
        if not self.history:
            print("No conversation history yet.")
            return
        print("\n--- Conversation History ---")
        for entry in self.history:
            print(f"[{entry['timestamp']}] User: {entry['user']}")
            print(f"[{entry['timestamp']}] Bot: {entry['bot']}")
        print("---------------------------\n")

