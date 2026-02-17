from __future__ import annotations

from typing import Annotated, Literal, TypedDict, Dict, Any
from langgraph.graph.message import add_messages
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_google_genai import ChatGoogleGenerativeAI

from .prompts import SEARCH_SYSTEM, OUTLINER_SYSTEM, WRITER_SYSTEM


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def _create_agent(llm, tools, system_message: str):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_message}"),
            MessagesPlaceholder(variable_name="messages"),
        ]
    ).partial(system_message=system_message)

    if tools:
        return prompt | llm.bind_tools(tools)
    return prompt | llm


def build_graph(*, model: str = "gemini-2.5-flash", tavily_max_results: int = 5):
    tools = [TavilySearchResults(max_results=tavily_max_results)]
    tool_node = ToolNode(tools)

    llm = ChatGoogleGenerativeAI(model=model)

    search_agent = _create_agent(llm, tools, SEARCH_SYSTEM)
    outliner_agent = _create_agent(llm, [], OUTLINER_SYSTEM)
    writer_agent = _create_agent(llm, [], WRITER_SYSTEM)

    def agent_node(state: AgentState, agent, name: str) -> Dict[str, Any]:
        result = agent.invoke(state)
        return {"messages": [result]}

    import functools
    search_node = functools.partial(agent_node, agent=search_agent, name="search")
    outliner_node = functools.partial(agent_node, agent=outliner_agent, name="outliner")
    writer_node = functools.partial(agent_node, agent=writer_agent, name="writer")

    def should_search(state: AgentState) -> Literal["tools", "outliner"]:
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "tools"
        return "outliner"

    workflow = StateGraph(AgentState)
    workflow.add_node("search", search_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("outliner", outliner_node)
    workflow.add_node("writer", writer_node)

    workflow.set_entry_point("search")
    workflow.add_conditional_edges("search", should_search)
    workflow.add_edge("tools", "search")
    workflow.add_edge("outliner", "writer")
    workflow.add_edge("writer", END)

    return workflow.compile()


def stream_run(graph, user_prompt: str, *, stream_mode: str = "values"):
    from langchain_core.messages import HumanMessage
    input_message = HumanMessage(content=user_prompt)
    for event in graph.stream({"messages": [input_message]}, stream_mode=stream_mode):
        yield event
