from typing import TypedDict, Annotated, List, Optional
from langgraph.graph import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from chat_service.tools.doc_tool import PortfolioDocTool
import os
import json

# Define the State
class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    input_type: str  # "voice" or "text"
    is_skill_query: bool
    context: Optional[str]
    final_response: Optional[str]
    audio: Optional[str]
    session_id: Optional[str]

# Initialize LLM and Tools
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
doc_tool = PortfolioDocTool()

# --- AGENT 1: The Input Classifier & Router ---
def agent_classifier(state: AgentState):
    """Classifies the input and determines the route."""
    messages = state["messages"]
    last_message = messages[-1].content
    
    prompt = f"""
    Analyze the user input and determine:
    1. Is it a query about skills, portfolio, experience, or professional background? (is_skill_query: true/false)
    2. Should the output be optimized for voice? (input_type: "voice" or "text") - Use "voice" if the user mentions speaking, listening, or if the incoming state is already voice.
    
    Return JSON only: {{"is_skill_query": bool, "input_type": "voice" | "text"}}
    User Input: {last_message}
    """
    
    res = llm.invoke([SystemMessage(content=prompt)])
    try:
        data = json.loads(res.content)
    except:
        data = {"is_skill_query": True, "input_type": state.get("input_type", "text")}
        
    return {
        "is_skill_query": data["is_skill_query"], 
        "input_type": data["input_type"]
    }

# --- AGENT 2: The Document Expert (Pure Agentic) ---
async def agent_document_expert(state: AgentState):
    """Answers using the portoflio knowledge base."""
    query = state["messages"][-1].content
    
    # Agent decides to search
    context = await doc_tool.search_portfolio(query)
    
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
    
    return {"final_response": res.content, "context": context}

# --- DATA FLOW SUPERVISOR (Fallback/General Chat) ---
def agent_supervisor(state: AgentState):
    """Handles general queries without document search."""
    query = state["messages"][-1].content
    prompt = "You are a friendly assistant for Abhijith's portfolio. Handle general greetings or non-skill queries politely."
    
    res = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=query)
    ])
    
    return {"final_response": res.content}

# --- REVIEWER / POST-PROCESSOR ---
def agent_reviewer(state: AgentState):
    """Reviews and refines the response."""
    response = state.get("final_response", "")
    input_type = state.get("input_type", "text")
    
    prompt = f"""
    Review the following response for Abhijith's portfolio.
    Ensure it is professional, accurate, and concise.
    If input_type is 'voice', make sure it's easy to listen to (no complex formatting, short sentences).
    
    Target Input Type: {input_type}
    Response: {response}
    
    Return the refined response.
    """
    
    res = llm.invoke([SystemMessage(content=prompt)])
    return {"final_response": res.content}

# --- AGENT 3: Voice Synthesis Engine ---
from openai import OpenAI
import base64

async def agent_voice_engine(state: AgentState):
    """Generates audio if input_type is voice."""
    if state.get("input_type") != "voice":
        return {}
        
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    text = state.get("final_response", "")
    
    try:
        res = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text[:4096] # Limit for TTS
        )
        audio_base64 = base64.b64encode(res.content).decode('utf-8')
        return {"audio": audio_base64}
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        return {"audio": None}
