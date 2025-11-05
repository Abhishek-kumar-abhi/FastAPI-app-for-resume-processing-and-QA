# Resume Processor API

## Overview

This project is a FastAPI application designed to streamline the initial stages of a recruitment pipeline. It allows for the uploading of resumes (in .pdf or .docx format), automatically extracts key information using a Hugging Face machine learning model, and stores the data in a structured format. The application leverages Supabase for file storage and metadata, and MongoDB to store the extracted candidate details. It also provides API endpoints to query the stored data, including a natural language Q&A endpoint.

## Features

- **Resume Upload**: Endpoint to upload resume files in PDF or DOCX format.
- **Structured Data Extraction**: Automatically extracts fields like education, work experience, skills, and more using a Hugging Face language model.
- **Supabase Integration**: Securely stores uploaded resume files in Supabase Storage and metadata in a Supabase table.
- **MongoDB Storage**: Stores the extracted structured data in a MongoDB collection for easy querying.
- **Candidate API**: Endpoints to list all candidates and retrieve the full details of a specific candidate.
- **Q&A Endpoint**: Ask natural language questions about a candidate's resume (e.g., "When did they graduate?").

## Architecture

The application is built with the following components:

- **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python.
- **Supabase**: Used as a backend-as-a-service for:
    - **Storage**: Storing the uploaded resume files.
    - **Database**: Storing metadata about the uploaded files (filename, upload time, storage URL).
- **MongoDB**: A NoSQL database used to store the structured candidate data extracted from the resumes.
- **Hugging Face**: Provides the machine learning models for:
    - **Information Extraction**: A text generation model is used to parse the resume text and extract information in a JSON format.
    - **Question Answering**: A QA model is used to answer natural language questions based on the extracted resume data.

## Getting Started

Follow these instructions to set up and run the project on your local machine.

### Prerequisites

- Python 3.8+
- pip
- virtualenv (recommended)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**
    Create a file named `.env` in the root of the project and add the following environment variables. You can use the `sample.env` file as a template.

    ```
    SUPABASE_URL="your_supabase_url"
    SUPABASE_KEY="your_supabase_api_key"
    SUPABASE_BUCKET="resumes"

    MONGO_URI="your_mongodb_connection_string"
    MONGO_DB="resumes_db"

    HF_API_KEY="your_huggingface_api_key"
    HF_EXTRACT_MODEL="google/flan-t5-large"
    HF_QA_MODEL="google/flan-t5-large"
    ```

### Running the Application

Once the setup is complete, you can run the application using `uvicorn`:

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Environment Variables

- `SUPABASE_URL`: The URL of your Supabase project.
- `SUPABASE_KEY`: The `anon` or `service_role` key for your Supabase project.
- `SUPABASE_BUCKET`: The name of the Supabase Storage bucket where resumes will be stored (default: `resumes`).
- `MONGO_URI`: The connection string for your MongoDB database.
- `MONGO_DB`: The name of the MongoDB database to use (default: `resumes_db`).
- `HF_API_KEY`: Your Hugging Face API key for accessing the inference API.
- `HF_EXTRACT_MODEL`: The name of the Hugging Face model to use for information extraction (default: `google/flan-t5-large`).
- `HF_QA_MODEL`: The name of the Hugging Face model to use for the Q&A endpoint (default: `google/flan-t5-large`).

## API Documentation

### POST /upload

Uploads a resume file. The file should be sent as multipart/form-data.

-   **Request:**
    ```
    POST /upload
    Content-Type: multipart/form-data

    file: (binary file data)
    ```

-   **Sample Response (Success):**
    ```json
    {
        "status": "ok",
        "metadata_id": "123",
        "mongo_id": "635f8f3b3e3f3f3f3f3f3f3f",
        "extracted_preview": {
            "skills": ["Python", "FastAPI", "MongoDB"],
            "education": [
                {
                    "institution": "University of Example",
                    "degree": "Bachelor of Science in Computer Science",
                    "start_date": "2018",
                    "end_date": "2022"
                }
            ],
            "experience": []
        }
    }
    ```

### GET /candidates

Lists all candidates with summary details.

-   **Request:**
    ```
    GET /candidates
    ```

-   **Sample Response:**
    ```json
    {
        "count": 1,
        "candidates": [
            {
                "candidate_id": "123",
                "file_name": "JohnDoe_Resume.pdf",
                "skills": ["Python", "FastAPI", "MongoDB"]
            }
        ]
    }
    ```

### GET /candidate/{candidate_id}

Retrieves the full information for a single candidate.

-   **Request:**
    ```
    GET /candidate/123
    ```

-   **Sample Response:**
    ```json
    {
        "candidate_id": "123",
        "education": [
            {
                "institution": "University of Example",
                "degree": "Bachelor of Science in Computer Science",
                "start_date": "2018",
                "end_date": "2022"
            }
        ],
        "experience": [],
        "skills": ["Python", "FastAPI", "MongoDB"],
        "hobbies": [],
        "certifications": [],
        "projects": [],
        "introduction": "A highly motivated software engineer...",
        "raw_text": "...",
        "metadata": {
            "file_name": "JohnDoe_Resume.pdf",
            "public_url": "https://...",
            "uploaded_at": "2025-11-05T12:00:00.000Z"
        },
        "created_at": "2025-11-05T12:00:00.000Z"
    }
    ```

### POST /ask/{candidate_id}

Asks a natural language question about a specific candidate.

-   **Request:**
    ```
    POST /ask/123
    Content-Type: application/json

    {
        "question": "When did this candidate finish graduation?"
    }
    ```

-   **Sample Response:**
    ```json
    {
        "question": "When did this candidate finish graduation?",
        "answer": "The candidate finished graduation in 2022."
    }
    ```

## Testing

To run the test suite, execute the following command in the root of the project:

```bash
python tests/test_basic.py
```
