import os
from supabase import create_client, Client
from dotenv import load_dotenv
import datetime

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

bucket_name = "resumes"
table_name = "resumes"

async def upload_resume(file_path: str, file_name: str):
    # Read file content
    with open(file_path, 'rb') as f:
        file_content = f.read()

    # Define a unique path for the file in Supabase storage
    storage_path = f"{os.path.splitext(file_name)[0]}_{datetime.datetime.now().timestamp()}{os.path.splitext(file_name)[1]}"

    # Upload the file to Supabase storage
    await supabase.storage.from_(bucket_name).upload(storage_path, file_content)

    # Get the public URL of the uploaded file
    public_url = supabase.storage.from_(bucket_name).get_public_url(storage_path)

    # Prepare metadata to be saved in the Supabase table
    metadata = {
        "file_name": file_name,
        "upload_time": str(datetime.datetime.now()),
        "storage_url": public_url
    }

    # Insert metadata into the Supabase table
    data, error = await supabase.table(table_name).insert(metadata).execute()

    if error:
        raise Exception(f"Error saving metadata to Supabase: {error}")

    # After insert, get the id
    response = await supabase.table(table_name).select("id").eq("storage_url", public_url).execute()
    if response.data:
        metadata_id = response.data[0]['id']
    else:
        raise Exception("Could not retrieve metadata id after insert.")


    return metadata_id, public_url