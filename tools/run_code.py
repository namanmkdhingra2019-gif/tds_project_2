from langchain_core.tools import tool
import subprocess
import os
import sys

def strip_code_fences(code: str) -> str:
    """Remove optional triple-backtick fences from a code string."""
    code = code.strip()
    if code.startswith("```"):
        lines = code.splitlines()
        # Drop first line (e.g. ``` or ```python)
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        # Drop last line if it is ```
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        code = "\n".join(lines)
    return code.strip()

@tool
def run_code(code: str) -> dict:
    """Execute Python code and return stdout, stderr, and return_code."""
    try:
        code = strip_code_fences(code)
        os.makedirs("LLMFiles", exist_ok=True)

        script_path = os.path.join("LLMFiles", "runner.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        proc = subprocess.run(
            [sys.executable, "runner.py"],
            capture_output=True,
            text=True,
            cwd="LLMFiles",
        )

        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "return_code": proc.returncode,
        }
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "return_code": -1}
