from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from agent.states.states import SingleAgentState
from agent.nodes.nodes import create_agent_node, should_continue
import os


def create_agent_graph(tools):
    """
    Creates an efficient single-agent graph with tool loop.

    Architecture:
    - Agent node: Plans, calls tools, and synthesizes (all in one)
    - Tools node: Executes tools
    - Simple loop: Agent can call tools multiple times

    Flow:
    User Query → Agent → Tool calls? → Tools → Agent (with results) → More tools? → Final Response
                    ↓ No tools                        ↓
                   End                            Loop back

    API Calls per query: 2-4 (instead of 11+)
    - 1st call: Agent decides which tools to call
    - Tool execution (no LLM cost)
    - 2nd call: Agent sees results, might call more tools or synthesize final response
    - Possible 3rd-4th calls if very complex multi-step analysis
    """

    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("AGENT_MODEL", "gemini-2.0-flash-exp"),
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)

    # Create agent node
    agent = create_agent_node(llm_with_tools)

    # Build the graph
    workflow = StateGraph(SingleAgentState)

    # Add nodes
    workflow.add_node("agent", agent)
    workflow.add_node("tools", ToolNode(tools))

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edge: agent decides to call tools or end
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )

    # After tools execute, loop back to agent
    workflow.add_edge("tools", "agent")

    return workflow.compile()
