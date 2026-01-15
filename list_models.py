import google.generativeai as genai
import os

key = "AIzaSyAw4JrwD6yMmLBCAcQ2KcNix2xtctnJmA8"
genai.configure(api_key=key)

print("Listing models...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
