from transformers import pipeline

# Inicializace pipeline pro generování textu
chatbot = pipeline("text-generation", model="TheBloke/Wizard-Vicuna-13B-Uncensored-SuperHOT-8K-GPTQ",device="cuda")

# Správa historie ručně
def chat_with_history():
    history = []
    print("Začněte konverzaci (napište 'konec' pro ukončení):")
    
    while True:
        user_input = input("Vy: ")
        if user_input.lower() == "konec":
            break
        
        # Přidání uživatelského vstupu do historie
        history.append(f"User: {user_input}")
        
        # Převedení historie na textový řetězec
        prompt = "\n".join(history) + "\nBot: "
        
        # Generování odpovědi
        response = chatbot(prompt, num_return_sequences=1, pad_token_id=chatbot.tokenizer.eos_token_id)
        bot_response = response[0]["generated_text"].split("Bot: ")[-1].strip()
        
        print(f"Bot: {bot_response}")
        
        # Přidání odpovědi bota do historie
        history.append(f"Bot: {bot_response}")
        
        # Volitelné: Zobrazení historie
        print(f"Historie: {history}")

if __name__ == "__main__":
    chat_with_history()