from langchain_classic.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .prompts import AGENT_SYSTEM


class ScriptedToolsModel(FakeMessagesListChatModel):
    """Keyless adapter for reproducible tool calls, never presented as model reasoning."""

    def bind_tools(self, tools, **kwargs):
        return self


def scripted_model(name, args=None, *, also=()):
    return ScriptedToolsModel(responses=[
        AIMessage(content="", tool_calls=[{"name": name, "args": args or {}, "id": "demo-1"},
            *({"name": extra, "args": {}, "id": f"demo-{index}"} for index, extra in enumerate(also, 2))]),
        AIMessage(content='{"claims":[]}'),
    ])


def make_executor(model, tools):
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=AGENT_SYSTEM),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    return AgentExecutor(agent=create_openai_tools_agent(model, tools, prompt),
                         tools=tools, max_iterations=4, handle_parsing_errors=True,
                         return_intermediate_steps=True)
