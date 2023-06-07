import os
import openai
import re
import requests
import tiktoken
import whisper
from common import get_valid_filename
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from urllib.parse import urlparse

load_dotenv(find_dotenv())

verbose = os.getenv('VERBOSE') or False
ENABLE_FP16 = os.getenv('FP16') or False
MAX_TOKENS = os.getenv('SUMMARY_MAX_TOKENS') or 100
TEMP_FOLDER = os.getenv('TEMP_FOLDER') or "temp"
temp_path = Path(TEMP_FOLDER)
temp_path.mkdir(parents=True, exist_ok=True)

print("Downloading model")
model = whisper.load_model("base")
encoding = tiktoken.get_encoding("p50k_base")
openai.api_key = os.getenv('OPENAI_API_KEY')

def get_audio_file(url):
    path = urlparse(url).path.rstrip("/")
    re_filename = re.compile(r"[/](?P<filename>[^/]+)[.](?P<ext>m4a|mp3|webm|mp4|mpga|wav|mpeg)$")
    m = re_filename.search(path)
    if not m:
        print("URL does not contain extension for supported audio formats: m4a|mp3|webm|mp4|mpga|wav|mpeg", url, sep="\n")
        return None
    filename = get_valid_filename(m.group("filename")) or "temp"
    filename += "." + m.group("ext")
    filepath = os.path.join(temp_path, filename)

    try:
        if verbose: print("Downloading from URL")
        headers = {      
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
        }  
        response = requests.get(url, headers=headers)
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
    
    if verbose: print("Transcribing")   
    result = model.transcribe(filepath, fp16=ENABLE_FP16)
    os.remove(filepath)
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


def summarize_text(text, max_tokens=MAX_TOKENS):
    summaries = []
    
    for chunk in break_up_text(text):
        if verbose: print("Summarizing")
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=chunk + "\n\nTl;dr",
            max_tokens=max_tokens,
            temperature=0
            )
        summary = response['choices'][0]['text'].strip().lstrip(": ")
        summaries.append(summary)

    return " ".join(summaries)

def summarize_audio_from_url(url):
    transcript = transcribe_audio(url)
    if not transcript:
        return None
    
    return summarize_text(transcript)