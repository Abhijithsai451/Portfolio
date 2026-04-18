from langgraph.graph import StateGraph, END
from chat_service.agents.definitions import (
    AgentState, 
    agent_classifier, 
    agent_document_expert, 
    agent_supervisor, 
    agent_reviewer, 
    agent_voice_engine
)

def create_graph():
    # Initialize the graph
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("classifier", agent_classifier)
    workflow.add_node("document_expert", agent_document_expert)
    workflow.add_node("supervisor", agent_supervisor)
    workflow.add_node("reviewer", agent_reviewer)
    workflow.add_node("voice_engine", agent_voice_engine)

    # Define Edges and Logic
    workflow.set_entry_point("classifier")

    def route_after_classifier(state: AgentState):
        if state["is_skill_query"]:
            return "document_expert"
        return "supervisor"

    workflow.add_conditional_edges(
        "classifier",
        route_after_classifier,
        {
            "document_expert": "document_expert",
            "supervisor": "supervisor"
        }
    )

    workflow.add_edge("document_expert", "reviewer")
    workflow.add_edge("supervisor", "reviewer")

    def route_after_reviewer(state: AgentState):
        if state.get("input_type") == "voice":
            return "voice_engine"
        return END

    workflow.add_conditional_edges(
        "reviewer",
        route_after_reviewer,
        {
            "voice_engine": "voice_engine",
            END: END
        }
    )

    workflow.add_edge("voice_engine", END)

    # Compile the graph
    return workflow.compile()

# Singleton instance of the graph
portfolio_graph = create_graph()
