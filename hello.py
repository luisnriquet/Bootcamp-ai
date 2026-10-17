import os
from openai import OpenAI

c = OpenAI(base_url="https://api.groq.com/openai/v1",
           api_key=os.environ["GROQ_API_KEY"])
r = c.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Di hola en una frase."}])
print(r.choices[0].message.content)
print(r.usage)