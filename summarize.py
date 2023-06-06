import os
import openai
import re
import requests
import tiktoken
import whisper
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from urllib.parse import urlparse

load_dotenv(find_dotenv())

TEMP_FOLDER = os.getenv('TEMP_FOLDER') or "temp"
temp_path = Path(TEMP_FOLDER)
temp_path.mkdir(parents=True, exist_ok=True)

print("Downloading model")
model = whisper.load_model("base")
encoding = tiktoken.get_encoding("p50k_base")
openai.api_key = os.getenv('OPENAI_API_KEY')

def get_audio_file(url):
    path = urlparse(url).path.rstrip("/")
    re_filename = re.compile(r"[/](?P<filename>[^./]+)[.](?P<ext>m4a|mp3|webm|mp4|mpga|wav|mpeg)$")
    m = re_filename.search(path)
    if not m:
        print("URL does not contain extension for supported audio formats: m4a|mp3|webm|mp4|mpga|wav|mpeg", e, sep="\n")
        return None
    filename = m.group("filename") + "." + m.group("ext")
    filepath = os.path.join(temp_path, filename)

    try:
        print("Downloading from URL")
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(e)
        return None
        
    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath


def transcribe_audio(url):
    filepath = get_audio_file(url)
    if not filepath:
        return None 
    
    print("Transcribing")   
    result = model.transcribe(filepath)
    return result["text"]

def break_up_text(text, chunk_size=2000):
    tokens = encoding.encode(text)
    while len(tokens) > chunk_size:
        # Decode all remaining tokens under limit
        chunk = encoding.decode(tokens[:chunk_size])
        # Determine best point `i` to truncate text and yield 
        i = len(chunk) - 1
        while (chunk[i] != "\n") and (chunk[i-1:i+1] != ". "):
            i -= 1
        yield chunk[:i].strip().strip("\n")
        # Tokenize remaining text and append to beginning of remaining tokens
        tokens = encoding.encode(chunk[i:]) + tokens[chunk_size:]
    # Decode remaining tokens and yield text    
    yield encoding.decode(tokens).strip().strip("\n")

def summarize_audio_from_url(url):
    transcript = transcribe_audio(url)
    if not transcript:
        return None
    summaries = []
    
    for chunk in break_up_text(transcript):
        print("Summarizing")
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=chunk + "\n\nTl;dr",
            max_tokens= 100,
            temperature=0
            )
        summary = response['choices'][0]['text'].strip().lstrip(": ")
        summaries.append(summary)

    return " ".join(summaries)