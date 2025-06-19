import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
def load_prompt_template() -> str:
    with open("prompt_template.txt", "r") as f:
        return f.read()


def generate_response(user_input: str) -> str:
    prompt = load_prompt_template()
    full_prompt = prompt + f"\nUser: {user_input}\nAI:"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": full_prompt}],

        max_tokens=20
    )

    return response.choices[0].message.content.strip()
