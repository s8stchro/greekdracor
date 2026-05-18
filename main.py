import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import os

app = FastAPI(title="Greek DraCor Replica API")

# Load data at startup
with open('corpus_data.json', 'r', encoding='utf-8') as f:
    corpus_data = json.load(f)

# Helper to find play by ID
def find_play(play_id: str):
    for play in corpus_data:
        if play['id'] == play_id:
            return play
    return None

@app.get("/api/corpus")
async def get_corpus():
    # Return summary of all plays
    summary = []
    for play in corpus_data:
        summary.append({
            'id': play['id'],
            'title': play['title'],
            'author': play['author'],
            'metrics': play['metrics']
        })
    return summary

@app.get("/api/play/{play_id}")
async def get_play(play_id: str):
    play = find_play(play_id)
    if not play:
        raise HTTPException(status_code=404, detail="Play not found")
    return play

@app.get("/api/play/{play_id}/network")
async def get_play_network(play_id: str):
    play = find_play(play_id)
    if not play:
        raise HTTPException(status_code=404, detail="Play not found")
    return play['network']

@app.get("/")
async def read_index():
    return FileResponse('index.html')

# If I have other static files like app.js
@app.get("/{fname}")
async def get_static(fname: str):
    if os.path.exists(fname):
        return FileResponse(fname)
    raise HTTPException(status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
