# Architecture

1. Client uploads a resume .pdf or .docx to `/upload`.
2. FastAPI reads file, extracts plaintext (pdfplumber/docx).
3. App uploads binary to Supabase Storage and records metadata in `resumes_metadata` table.
4. App sends extracted text to a Hugging Face Inference model (HF Inference API) to parse structured fields.
5. Parsed candidate document stored in MongoDB `candidates` collection.
6. APIs `/candidates` and `/candidate/{id}` read from MongoDB.
7. `/ask/{candidate_id}` sends a question + candidate JSON to a Hugging Face LLM via Inference API and returns the LLM answer.
