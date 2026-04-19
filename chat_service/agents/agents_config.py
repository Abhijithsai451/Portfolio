from typing import TypedDict, Annotated, List, Optional
from langgraph.graph import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from chat_service.tools.doc_tool import PortfolioDocTool
import os
import json
from openai import OpenAI
import base64

# from main import logger


# Define the State
class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    input_type: str  # "voice" or "text"
    is_skill_query: bool
    context: Optional[str]
    final_response: Optional[str]
    audio: Optional[str]
    session_id: Optional[str]


import logging

# Initialize Logger
logger = logging.getLogger(__name__)

# Initialize LLM and Tools
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
doc_tool = PortfolioDocTool()


# --- AGENT 1: The Input Classifier & Router ---
def agent_classifier(state: AgentState):
    """Classifies the input and determines the route."""
    messages = state["messages"]
    last_message = messages[-1].content
    initial_input_type = state.get("input_type", "text")
    logger.info(f"Agent Classifier: Processing input - '{last_message[:50]}...' (Initial mode: {initial_input_type})")

    prompt = f"""
    Analyze the user input and determine:
    1. Is it a query about skills, portfolio, experience, projects, or professional background? (is_skill_query: true/false)
    2. Should the output be optimized for voice? (input_type: "voice" or "text")
    
    Constraint: If the current mode is "voice", keep it as "voice" unless the user explicitly asks for "text".
    
    Return JSON only: {{"is_skill_query": bool, "input_type": "voice" | "text"}}
    Current Mode: {initial_input_type}
    User Input: {last_message}
    """

    try:
        res = llm.invoke([SystemMessage(content=prompt)])
        data = json.loads(res.content)
        
        # Override with initial if it was voice and LLM flaked, or just respect initial voice
        if initial_input_type == "voice" and data.get("input_type") == "text":
            data["input_type"] = "voice"
            
        logger.info(f"Agent Classifier: Result - is_skill_query={data['is_skill_query']}, input_type={data['input_type']}")
    except Exception as e:
        logger.error(f"Agent Classifier Error: {str(e)}")
        data = {"is_skill_query": True, "input_type": initial_input_type}

    return {
        "is_skill_query": data["is_skill_query"],
        "input_type": data["input_type"]
    }


# --- AGENT 2: The Document Expert (Pure Agentic) ---
async def agent_document_expert(state: AgentState):
    """Answers using the Portflio knowledge base."""
    query = state["messages"][-1].content
    logger.info(f"Agent Document Expert: Answering query - '{query[:50]}...'")

    # Agent decides to search
    context = await doc_tool.search_portfolio(query)
    logger.info(f"Agent Document Expert: Retrieved context (length: {len(context)})")

    prompt = f"""
    You are Abhijith's Portfolio Assistant.
    Use the following retrieved context to answer the user's question accurately.
    Context: {context}
    
    If the context doesn't contain the answer, politely say you don't have that specific information but can talk about Abhijith's other skills.
    
    Keep it professional and concise.
    """

    res = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=query)
    ])
    logger.info("Agent Document Expert: Generated response.")

    return {"final_response": res.content, "context": context}


def agent_supervisor(state: AgentState):
    """Handles general queries without document search."""
    query = state["messages"][-1].content
    logger.info(f"Agent Supervisor: Handling general query - '{query[:50]}...'")
    prompt = "You are a friendly assistant for Abhijith's portfolio. Handle general greetings or non-skill queries politely."

    res = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=query)
    ])
    logger.info("Agent Supervisor: Generated response.")

    return {"final_response": res.content}


def agent_reviewer(state: AgentState):
    """Reviews and refines the response."""
    response = state.get("final_response", "")
    input_type = state.get("input_type", "text")
    logger.info(f"Agent Reviewer: Refining response for input_type='{input_type}'")

    prompt = f"""
    Review the following response for Abhijith's portfolio.
    Ensure it is professional, accurate, and concise.
    If input_type is 'voice', make sure it's easy to listen to (no complex formatting, short sentences).
    
    Target Input Type: {input_type}
    Response: {response}
    
    Return the refined response.
    """

    res = llm.invoke([SystemMessage(content=prompt)])
    logger.info("Agent Reviewer: Refinement complete.")
    return {"final_response": res.content}


async def agent_voice_engine(state: AgentState):
    """Generates audio if input_type is voice."""
    if state.get("input_type") != "voice":
        logger.info("Agent Voice Engine: Skipping (input_type is not voice)")
        return {}

    text = state.get("final_response", "")
    logger.info(f"Agent Voice Engine: Generating TTS for text (length: {len(text)})")

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        res = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text[:4096]  # Limit for TTS
        )
        audio_base64 = base64.b64encode(res.content).decode('utf-8')
        logger.info(f"Agent Voice Engine: Successfully generated audio (base64 length: {len(audio_base64)})")
        return {"audio": audio_base64}
    except Exception as e:
        logger.error(f"Agent Voice Engine Error: {str(e)}")
        return {"audio": None}
