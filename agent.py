"""
agent.py - LangGraph agent using OpenRouter (OpenAI-compatible) for TDS Quiz Solver
"""

import os
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from tools import (
    get_rendered_html,
    download_file,
    run_code,
    post_request,
    add_dependencies,
)

# LLM via OpenRouter (OpenAI-compatible API)
llm = ChatOpenAI(
    model="anthropic/claude-3.5-sonnet",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    extra_headers={
        "HTTP-Referer": "https://23f3000531-my-llm-project.hf.space",
        "X-Title": "TDS Quiz Solver",
    },
    temperature=0.1,
    max_tokens=400, 
)


tools = [get_rendered_html, download_file, run_code, post_request, add_dependencies]
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = f"""You are an autonomous quiz-solving agent for IITM TDS LLM-analysis.

IMPORTANT ENV VARS:
- EMAIL = {os.getenv('EMAIL', 'your_iitm_email@example.com')}
- SECRET = {os.getenv('SECRET', 'mynameisnaman')}

MISSION:
1. Use get_rendered_html() to read each quiz page
2. When page shows "POST this JSON to /submit", immediately call:
   post_request("https://tds-llm-analysis.s-anand.net/submit", {{
     "email": "{os.getenv('EMAIL', 'your_iitm_email@example.com')}",
     "secret": "{os.getenv('SECRET', 'mynameisnaman')}",
     "url": "/demo" (or whatever current page path is),
     "answer": "your analysis or answer here"
   }})
3. Check response: if "correct": true → extract "next" URL from response
4. Repeat until no more URLs or quiz says COMPLETE

Tools available:
- get_rendered_html(url): read JS-rendered quiz pages
- post_request(url, payload): submit JSON answers
- download_file(url, filename): download data files
- run_code(code): analyze CSV/data with Python
- add_dependencies(packages): install missing libs

Start now: get_rendered_html("https://tds-llm-analysis.s-anand.net/demo")"""


def agent_node(state: MessagesState):
    """Single LLM step with tool binding."""
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# Build LangGraph
graph = StateGraph(MessagesState)
graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(tools=tools))
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", tools_condition)
graph.add_edge("tools", "agent")

memory = MemorySaver()
app = graph.compile(checkpointer=memory)

async def run_agent(start_url: str) -> dict:
    print(f"🤖 LangGraph agent starting for URL: {start_url}")
    initial_messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Start solving the TDS quiz chain from this URL: {start_url}"),
    ]
    config = {
        "configurable": {"thread_id": f"quiz_{hash(start_url)}"},
        "recursion_limit": 50  # raise from default 25
    }

    try:
        async for event in app.astream({"messages": initial_messages}, config, stream_mode="values"):
            last = event["messages"][-1]
            print(f"🧠 Agent step: {str(last.content)[:200]}")
        print("✅ Agent finished quiz chain")
        return {"status": "completed"}
    except Exception as e:
        print(f"❌ Agent error: {e}")
        return {"status": "failed", "error": str(e)}
