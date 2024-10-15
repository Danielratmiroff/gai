import os

from groq import Groq

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Explain the importance of fast language models",
        }
    ],
    model="llama3-8b-8192",
    temperature=1,
    max_tokens=2048,
    top_p=1,
    stream=False,
    response_format={"type": "json_object"},
    stop=None,
)

print(chat_completion.choices[0].message.content)
