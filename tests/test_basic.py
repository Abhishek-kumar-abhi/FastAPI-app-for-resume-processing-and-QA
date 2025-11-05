import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the parent directory to the sys.path to allow imports from the main project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extractor import call_hf_extractor, extract_text_from_file
from main import app
from fastapi.testclient import TestClient

class TestExtractor(unittest.TestCase):

    @patch('requests.post')
    def test_call_hf_extractor_success(self, mock_post):
        # Mock the response from the Hugging Face API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            'generated_text': '''
            {
                "introduction": "This is a test introduction.",
                "education": [{"institution": "Test University", "degree": "B.Sc.", "start_date": "2020", "end_date": "2024"}],
                "experience": [],
                "skills": ["Python", "FastAPI"],
                "projects": [],
                "certifications": [],
                "hobbies": []
            }
            '''
        }]
        mock_post.return_value = mock_response

        # Call the function with some dummy text
        resume_text = "This is a test resume."
        hf_api_key = "test_api_key"
        extracted_data = call_hf_extractor(resume_text, hf_api_key)

        # Assert that the data was extracted and parsed correctly
        self.assertEqual(extracted_data['introduction'], "This is a test introduction.")
        self.assertEqual(len(extracted_data['education']), 1)
        self.assertEqual(extracted_data['education'][0]['institution'], "Test University")
        self.assertEqual(len(extracted_data['skills']), 2)
        self.assertIn("Python", extracted_data['skills'])

    @patch('requests.post')
    def test_call_hf_extractor_api_error(self, mock_post):
        # Mock a failed response from the Hugging Face API
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        # Call the function and assert that it raises a RuntimeError
        with self.assertRaises(RuntimeError):
            call_hf_extractor("some text", "some_key")

    def test_extract_text_from_file_unsupported(self):
        # Test that an unsupported file type raises a ValueError
        with self.assertRaises(ValueError):
            extract_text_from_file(b"some bytes", "test.txt")


class TestAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    @patch('main.upload_resume')
    @patch('main.extract_text_from_file')
    @patch('main.call_hf_extractor')
    @patch('main.mongo')
    def test_upload_endpoint_success(self, mock_mongo, mock_call_hf, mock_extract_text, mock_upload_resume):
        # Mock the return values of the helper functions
        mock_upload_resume.return_value = ("mock_metadata_id", "mock_public_url")
        mock_extract_text.return_value = "This is the resume text."
        mock_call_hf.return_value = {"skills": ["python", "fastapi"]}
        mock_mongo.insert_candidate.return_value = "mock_mongo_id"

        # Create a dummy file for upload
        dummy_file_content = b"dummy pdf content"
        dummy_file_name = "test_resume.pdf"
        
        with open(dummy_file_name, "wb") as f:
            f.write(dummy_file_content)

        with open(dummy_file_name, "rb") as f:
            response = self.client.post("/upload", files={"file": (dummy_file_name, f, "application/pdf")})

        os.remove(dummy_file_name)

        # Assert the response
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json['status'], "ok")
        self.assertEqual(response_json['metadata_id'], "mock_metadata_id")
        self.assertEqual(response_json['mongo_id'], "mock_mongo_id")
        self.assertIn("python", response_json['extracted_preview']['skills'])

    def test_upload_endpoint_invalid_file_type(self):
        dummy_file_content = b"dummy txt content"
        dummy_file_name = "test.txt"

        with open(dummy_file_name, "wb") as f:
            f.write(dummy_file_content)

        with open(dummy_file_name, "rb") as f:
            response = self.client.post("/upload", files={"file": (dummy_file_name, f, "text/plain")})
        
        os.remove(dummy_file_name)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['detail'], "Only PDF and DOCX uploads are allowed")


if __name__ == '__main__':
    unittest.main()
