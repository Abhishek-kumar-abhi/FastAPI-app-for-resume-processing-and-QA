ALLOWED_EXTS = {'.pdf', '.docx', '.doc'}
ALLOWED_MIMES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword'
}

def validate_file_type(filename: str, content_type: str) -> bool:
    lower = filename.lower()
    for ext in ALLOWED_EXTS:
        if lower.endswith(ext):
            return True
    if content_type in ALLOWED_MIMES:
        return True
    return False
