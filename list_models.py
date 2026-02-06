import google.generativeai as genai
import os

key = "AIzaSyCxdAZQpLXXYTlFKPmKojnLchkIwqTecwo"
genai.configure(api_key=key)

print("Listing models...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
