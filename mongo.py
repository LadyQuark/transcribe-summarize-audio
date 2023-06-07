import pymongo
import os
import csv
from common import write_csv
from dotenv import load_dotenv, find_dotenv
from summarize import transcribe_audio, summarize_text
from tqdm import tqdm

load_dotenv(find_dotenv())

# Connect to MongoDB
MONGO_HOST = os.getenv('MONGO_HOST')
MONGO_PORT = int(os.getenv('MONGO_PORT'))
MONGO_DB = os.getenv('MONGO_DB')
client = pymongo.MongoClient(MONGO_HOST, port=MONGO_PORT)
db = client[MONGO_DB]

knowledgeitem_master = db['knowledgeitem_master']
braintech_master = db['braintech_master']

def update_all_podcast_transcript_summary():
    query = {
        "$and": [
            {"metadata.audio_file": {"$ne": None}}, 
            {"metadata.audio_file": {"$ne": ""}}, 
            {"tags": "podcast"},
        ],
        "$or": [
            {"metadata.transcript": {"$eq": None}}, 
            {"metadata.transcript": {"$eq": ""}}, 
        ]
    }
    project = {
        "_id": 1,
        "metadata.audio_file": 1
    }
    docs = list(knowledgeitem_master.find(query, project))
    update_count = 0
    failed_count = 0 
    pbar = tqdm(docs)
    
    for doc in pbar:
        # Transcribe
        pbar.set_description("Transcribing")
        text = transcribe_audio(doc['metadata']['audio_file'])
        if not text:
            failed_count += 1
            write_csv("failed.csv", {"id": doc['_id'], 'audio_file': doc['metadata']['audio_file']})
            continue
        
        # Summarize
        pbar.set_description("Summarizing")
        summary = summarize_text(text)

        # Update in MongoDB
        pbar.set_description("Updating MongoDB")
        update_results = knowledgeitem_master.update_one(
            {"_id": doc['_id']},
            {"$set": {
                "metadata.transcript": text,
                "metadata.summary": summary
                }
            }
        )
        # Append results to CSV
        if update_results.modified_count > 0:
            update_count += 1
            write_csv("updated.csv", {"id": doc['_id']})
    
    print("\nUpdated:", update_count)
    print("Failed:", failed_count)

