from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

from app.services.ai.chains import resume_chat_intent_chain
from app.services.ai.schemas import ResumeChatIntentResult


ResumeAgentRoute = Literal[
    "answer",
    "propose_change",
    "apply_change",
    "reject_change",
    "missing_pending_change",
]


class ResumeAgentState(TypedDict, total=False):
    """State shared by the resume agent's turn-planning graph."""

    payload: dict[str, Any]
    pending_change_available: bool
    intent: ResumeChatIntentResult
    route: ResumeAgentRoute


class ResumeAgentPlan(BaseModel):
    """A deterministic execution plan consumed by the chat service tools."""

    route: ResumeAgentRoute
    intent: ResumeChatIntentResult
    pending_change_available: bool = False
    requires_confirmation: bool = False


def _understand_intent_node(state: ResumeAgentState) -> ResumeAgentState:
    return {"intent": resume_chat_intent_chain(state["payload"])}


def _route_after_intent(state: ResumeAgentState) -> str:
    intent = state["intent"].intent
    if intent == "confirm_change":
        return "apply_change" if state.get("pending_change_available") else "missing_pending_change"
    if intent == "reject_change":
        return "reject_change" if state.get("pending_change_available") else "missing_pending_change"
    if intent in {"answer", "clarify"}:
        return "answer"
    return "propose_change"


def _route_node(route: ResumeAgentRoute):
    def node(_: ResumeAgentState) -> ResumeAgentState:
        return {"route": route}

    return node


@lru_cache(maxsize=1)
def build_resume_agent_graph():
    """Compile the stable planning graph once per backend process."""

    graph = StateGraph(ResumeAgentState)
    graph.add_node("understand_intent", _understand_intent_node)

    route_nodes: tuple[ResumeAgentRoute, ...] = (
        "answer",
        "propose_change",
        "apply_change",
        "reject_change",
        "missing_pending_change",
    )
    for route in route_nodes:
        graph.add_node(route, _route_node(route))
        graph.add_edge(route, END)

    graph.add_edge(START, "understand_intent")
    graph.add_conditional_edges(
        "understand_intent",
        _route_after_intent,
        {route: route for route in route_nodes},
    )
    return graph.compile()


def plan_resume_agent_turn(
    payload: dict[str, Any],
    *,
    pending_change_available: bool,
) -> ResumeAgentPlan:
    """Classify one user turn and select the only allowed next action."""

    state: ResumeAgentState = {
        "payload": payload,
        "pending_change_available": pending_change_available,
    }
    result = build_resume_agent_graph().invoke(state)
    route = result.get("route")
    intent = result.get("intent")
    if route is None or intent is None:
        raise RuntimeError("Resume agent did not produce an executable plan")
    return ResumeAgentPlan(
        route=route,
        intent=intent,
        pending_change_available=pending_change_available,
        requires_confirmation=route == "propose_change",
    )
