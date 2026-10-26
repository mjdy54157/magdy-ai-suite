from groq import Groq
client = Groq()
completion = client.chat.completions.create(model='qwen/qwen3.8-27b', messages=[{'role': 'user', 'content': 'Hello! Introduce yourself as a local developer assistant for Magdy.'}])
print(completion.choices[0].message.content)
