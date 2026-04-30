import os
from dotenv import load_dotenv
import spacy
import pdfplumber
from rapidfuzz import fuzz
import requests

# 1. Test .env loading
load_dotenv()
token = os.getenv('TELEGRAM_BOT_TOKEN')
print(f"1. Telegram Token Loaded: {'YES' if token else 'NO (Check .env file)'}")

# 2. Test spaCy
try:
    nlp = spacy.load("en_core_web_sm")
    doc = nlp("This is a test of the NLP pipeline.")
    print("2. spaCy Model Loaded: YES")
except Exception as e:
    print(f"2. spaCy Model Loaded: NO ({e})")

# 3. Test Ollama (Assumes Ollama is running in the background)
try:
    response = requests.post('http://localhost:11434/api/generate', 
                             json={"model": "llama3:8b-instruct-q4_0", "prompt": "Say the word 'Acknowledged'.", "stream": False})
    if response.status_code == 200:
        print(f"3. Local Ollama Inference: SUCCESS ({response.json()['response'].strip()})")
    else:
        print("3. Local Ollama Inference: FAILED (Check if Ollama app is running)")
except Exception as e:
    print("3. Local Ollama Inference: FAILED (Check if Ollama app is running)")