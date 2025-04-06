import openai
import os
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_trump_response(user_input):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # or "gpt-3.5-turbo" if you don't have GPT-4 access
        messages=[
            {"role": "system", "content": "You are Donald Trump. Respond in his unique voice, style, and attitude. Be confident, opinionated, and dramatic."},
            {"role": "user", "content": user_input}
        ]
    )
    return response["choices"][0]["message"]["content"]

# Simple chat loop
if __name__ == "__main__":
    print("💬 Trump is ready. Type your question (or 'exit' to stop):")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Trump's tired of talking to you. Goodbye.")
            break
        response = get_trump_response(user_input)
        print("Trump:", response)

