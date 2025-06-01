import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StreamableChatBot:
    def __init__(self, model_id="gpt2"):
        """Initialize the chatbot with a specified model and conversation history."""
        self.model_id = "UnfilteredAI/NSFW-3B"
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.history = []  # List to store conversation history
        self.max_history_length = 10  # Limit history to last 5 exchanges
        self.load_model()

    def load_model(self):
        """Load the pre-trained model and tokenizer."""
        try:
            logger.info(f"Loading model: {self.model_id}")
           # self.model = AutoModelForCausalLM.from_pretrained(
           #     self.model_id,
           #     use_safetensors=True,trust_remote_code=True
           # ).to(self.device)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id,use_safetensors=True,trust_remote_code=True)
            self.tokenizer.pad_token = self.tokenizer.eos_token
            logger.info("Model and tokenizer loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model {self.model_id}: {str(e)}")
            raise

    def add_to_history(self, user_input, response):
        """Add a user input and bot response to the conversation history."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history.append({"timestamp": timestamp, "user": user_input, "bot": response})
        # Keep only the last max_history_length exchanges
        if len(self.history) > self.max_history_length:
            self.history = self.history[-self.max_history_length:]
        logger.debug(f"Updated history: {self.history}")

    def get_history_context(self):
        """Build a context string from the conversation history."""
        context = ""
        for entry in self.history:
            context += f"User: {entry['user']}\nBot: {entry['bot']}\n"
        return context

    def generate_streaming_response(self, user_input, max_length=100, temperature=0.7):
        """Generate a streaming response to the user input, incorporating history."""
        if not user_input.strip():
            logger.error("No input provided")
            yield {"error": "Please provide a valid input"}
            return

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
                    outputs = self.model(generated_ids, attention_mask=attention_mask, max_new_tokens=1 + input_ids.shape[1],stop_strings=["Bot","\n"],generate_full_text=False)
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
            self.add_to_history(user_input, generated_text.strip())

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

def main():
    """Main function to run the chatbot in a command-line interface with streaming."""
    chatbot = StreamableChatBot(model_id="Novaciano/NSFW-AMEBA-3.2-1B")  # Change to "Novaciano/NSFW-AMEBA-3.2-1B" if desired
    print("Welcome to the Streamable ChatBot! Type 'quit' to exit or 'history' to view conversation history.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
        elif user_input.lower() == 'history':
            chatbot.display_history()
            continue

        print("Bot: ", end="", flush=True)
        full_response = ""
        for response in chatbot.generate_streaming_response(user_input):
            if "error" in response:
                print(f"\nError: {response['error']}")
                break
            new_text = response["result"][len(full_response):]
            print(new_text, end="", flush=True)
            full_response = response["result"]
        print()  # Newline after streaming completes

if __name__ == "__main__":
    main()