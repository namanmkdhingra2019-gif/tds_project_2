from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import time
import asyncio

from agent import run_agent  


app = FastAPI()


@app.get("/")
async def root(request: Request):
    # Hugging Face often calls "/?logs=container" to show logs
    if request.query_params.get("logs") == "container":
        return {"status": "ok", "message": "container logs endpoint for HF"}
    return {"message": "TDS Quiz Solver is running"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EMAIL = os.getenv("EMAIL", "")
SECRET = os.getenv("SECRET", "")
START_TIME = time.time()

@app.get("/healthz")
async def healthz():
    return {
        "status": "ok",
        "uptime": int(time.time() - START_TIME),
        "email_set": bool(EMAIL),
        "secret_set": bool(SECRET)
    }

@app.get("/demo")
async def demo():
    """Simple demo endpoint"""
    return {"message": "TDS Quiz Solver is LIVE!", "status": "ready"}

@app.post("/solve")
async def solve(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    url = data.get("url")
    secret = data.get("secret")

    if not url or not secret:
        raise HTTPException(400, "Missing url or secret")
    if secret != SECRET:
        raise HTTPException(403, "Invalid secret")

    print(f"🚀 Starting quiz: {url}")

    # run the async agent in the background so /solve returns quickly
    async def _runner(u: str):
        await process_quiz(u)

    background_tasks.add_task(asyncio.run, _runner(url))
    return {"status": "ok", "message": "Agent started"}


async def process_quiz(url: str):
    """Run the LangGraph agent instead of raw Playwright."""
    print("🔁 process_quiz started (agent mode)")
    try:
        result = await run_agent(url)
        print(f"✅ Agent finished with result: {result}")
    except Exception as e:
        print(f"❌ Error in process_quiz/agent: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
