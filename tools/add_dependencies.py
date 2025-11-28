from langchain_core.tools import tool
import subprocess

@tool  
def add_dependencies(packages: list) -> str:
    """Install Python packages."""
    try:
        subprocess.check_call(["pip", "install"] + packages)
        return f"Installed: {', '.join(packages)}"
    except Exception as e:
        return f"Error: {str(e)}"
