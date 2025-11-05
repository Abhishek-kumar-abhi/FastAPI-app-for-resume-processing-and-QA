import io
import json
from typing import Dict
import re

import pdfplumber
import docx
import requests

HF_INFERENCE_URL = "https://api-inference.huggingface.co/models/"

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    lower = filename.lower()
    if lower.endswith('.pdf'):
        return extract_text_from_pdf(file_bytes)
    elif lower.endswith('.docx') or lower.endswith('.doc'):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError("Unsupported file type")

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            ptext = page.extract_text()
            if ptext:
                text.append(ptext)
    return "\n".join(text)

def extract_text_from_docx(file_bytes: bytes) -> str:
    document = docx.Document(io.BytesIO(file_bytes))
    lines = []
    for para in document.paragraphs:
        if para.text:
            lines.append(para.text)
    return "\n".join(lines)

def call_hf_extractor(text: str, hf_api_key: str, model: str = "google/flan-t5-large") -> Dict:
    prompt = f'''
Extract the following information from the resume text provided below.
Return the information as a valid JSON object. Do not include any text before or after the JSON object.

The JSON object should have the following keys:
- "introduction": A brief introduction of the candidate.
- "education": A list of education objects. Each object should have the keys "institution", "degree", "start_date", and "end_date".
- "experience": A list of experience objects. Each object should have the keys "company", "position", "start_date", "end_date", and "description".
- "skills": A list of strings, where each string is a skill.
- "projects": A list of strings, where each string is a project description.
- "certifications": A list of strings, where each string is a certification.
- "hobbies": A list of strings, where each string is a hobby.

If any information is not found, return an empty list or an empty string for the corresponding key.

Resume text:
---
{text}
---

JSON output:
'''

    headers = {"Authorization": f"Bearer {hf_api_key}", "Accept": "application/json"}
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}

    resp = requests.post(HF_INFERENCE_URL + model, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"HF API error: {resp.status_code} {resp.text}")

    out = resp.json()
    generated = None
    if isinstance(out, list) and len(out) > 0 and 'generated_text' in out[0]:
        generated = out[0]['generated_text']
    elif isinstance(out, dict) and 'generated_text' in out:
        generated = out['generated_text']
    else:
        generated = json.dumps(out)

    try:
        # Use regex to find the JSON object
        json_match = re.search(r'\{.*\}', generated, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            # The model sometimes returns a JSON object with escaped characters.
            # The json.loads function can handle this.
            parsed = json.loads(json_str)
        else:
            # fallback to old parsing logic
            try:
                parsed = json.loads(generated)
            except Exception:
                import ast
                parsed = ast.literal_eval(generated)

    except Exception:
        parsed = {
            "education": [],
            "experience": [],
            "skills": [],
            "hobbies": [],
            "certifications": [],
            "projects": [],
            "introduction": "Could not parse extracted data.",
            "error_info": generated
        }
    return parsed

def call_hf_llm(question: str, context_json: str, hf_api_key: str, model: str = "google/flan-t5-large") -> str:
    prompt = (
        "You are an assistant answering questions about a candidate.\n"
        "Use ONLY the provided JSON context to answer. If information is not present, say 'Information not found'.\n\n"
        "Context JSON:\n" + context_json + "\n\nQuestion:\n" + question + "\n\nAnswer:"
    )

    headers = {"Authorization": f"Bearer {hf_api_key}", "Accept": "application/json"}
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}
    resp = requests.post(HF_INFERENCE_URL + model, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"HF API error: {resp.status_code} {resp.text}")
    out = resp.json()

    if isinstance(out, list) and len(out) > 0 and 'generated_text' in out[0]:
        return out[0]['generated_text'].strip()
    if isinstance(out, dict) and 'generated_text' in out:
        return out['generated_text'].strip()
    return str(out)