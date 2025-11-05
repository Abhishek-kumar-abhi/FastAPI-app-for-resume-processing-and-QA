import os
import io
import uuid
import json
from datetime import datetime
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from supabase_helper import upload_resume
from mongodb_helper import MongoDBClient
from extractor import extract_text_from_file, call_hf_extractor, call_hf_llm
from utils import validate_file_type

load_dotenv()

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "resumes")
HF_API_KEY = os.getenv("HF_API_KEY")
HF_EXTRACT_MODEL = os.getenv("HF_EXTRACT_MODEL", "google/flan-t5-large")
HF_QA_MODEL = os.getenv("HF_QA_MODEL", "google/flan-t5-large")
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "resumes_db")

REQUIRED = [SUPABASE_URL, SUPABASE_KEY, HF_API_KEY, MONGO_URI]
if not all(REQUIRED):
    raise RuntimeError("Missing one or more required environment variables. See sample.env")

app = FastAPI(title="Resume Processor")

mongo = MongoDBClient(MONGO_URI, MONGO_DB)

class AskRequest(BaseModel):
    question: str

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    # Validate file content type and extension
    if not validate_file_type(file.filename, file.content_type):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX uploads are allowed")

    # Save the uploaded file to a temporary file
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    temp_file_path = os.path.join(temp_dir, file.filename)
    with open(temp_file_path, "wb") as f:
        f.write(await file.read())

    # Extract plaintext from resume
    try:
        # we need to re-read the file for extract_text_from_file as it expects bytes
        with open(temp_file_path, "rb") as f:
            contents = f.read()
        text = extract_text_from_file(contents, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {e}")
    
    # Upload file to Supabase storage and save metadata
    try:
        metadata_id, public_url = await upload_resume(temp_file_path, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase upload failed: {e}")
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    # Call Hugging Face extractor
    try:
        extracted = call_hf_extractor(text, HF_API_KEY, model=HF_EXTRACT_MODEL)
    except Exception as e:
        extracted = {"error": str(e)}

    candidate_doc = {
        "candidate_id": metadata_id,
        "education": extracted.get("education", []),
        "experience": extracted.get("experience", []),
        "skills": extracted.get("skills", []),
        "hobbies": extracted.get("hobbies", []),
        "certifications": extracted.get("certifications", []),
        "projects": extracted.get("projects", []),
        "introduction": extracted.get("introduction", ""),
        "raw_text": text,
        "metadata": { # creating a metadata dict for mongo
            "file_name": file.filename,
            "public_url": public_url,
            "uploaded_at": datetime.utcnow().isoformat()
        },
        "created_at": datetime.utcnow().isoformat()
    }

    insert_resp = await mongo.insert_candidate(candidate_doc)

    return JSONResponse({
        "status": "ok",
        "metadata_id": metadata_id,
        "mongo_id": str(insert_resp),
        "extracted_preview": {
            "skills": candidate_doc["skills"],
            "education": candidate_doc["education"],
            "experience": candidate_doc["experience"]
        }
    })

@app.get("/candidates")
async def list_candidates():
    docs = await mongo.list_candidates_summary()
    return {"count": len(docs), "candidates": docs}

@app.get("/candidate/{candidate_id}")
async def get_candidate(candidate_id: str):
    doc = await mongo.get_candidate_by_id(candidate_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return doc

@app.post("/ask/{candidate_id}")
async def ask_candidate(candidate_id: str, req: AskRequest):
    doc = await mongo.get_candidate_by_id(candidate_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Candidate not found")

    context = json.dumps({
        "education": doc.get("education"),
        "experience": doc.get("experience"),
        "skills": doc.get("skills"),
        "projects": doc.get("projects"),
        "certifications": doc.get("certifications"),
        "hobbies": doc.get("hobbies"),
        "introduction": doc.get("introduction"),
    })

    answer = call_hf_llm(req.question, context, HF_API_KEY, model=HF_QA_MODEL)
    return {"question": req.question, "answer": answer}