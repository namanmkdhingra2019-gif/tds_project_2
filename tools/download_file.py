from langchain_core.tools import tool
import requests
import os

@tool
def download_file(url: str, filename: str) -> str:
    """Download file from URL."""
    try:
        os.makedirs("LLMFiles", exist_ok=True)
        path = f"LLMFiles/{filename}"
        response = requests.get(url)
        response.raise_for_status()
        
        with open(path, "wb") as f:
            f.write(response.content)
        return f"Saved: {filename}"
    except Exception as e:
        return f"Error: {str(e)}"
