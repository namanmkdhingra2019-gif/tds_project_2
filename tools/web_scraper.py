from langchain_core.tools import tool
from playwright.sync_api import sync_playwright

@tool
def get_rendered_html(url: str) -> str:
    """Get fully rendered HTML from JS-heavy pages."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        return f"Error: {str(e)}"
