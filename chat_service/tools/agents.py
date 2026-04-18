from typing import TypedDict, Annotated, List

from langgraph.graph import add_messages


class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    response_mode: str
    is_skill_query: bool


def input_classifier_agent(state: AgentState):
    pass
