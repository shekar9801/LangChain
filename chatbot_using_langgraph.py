# from langchain.chat_models import ChatOllama
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
import sqlite3

model = ChatOllama(model='gpt-oss:20b')

search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def calculator(first_num: float, second_num: float, operation:str)->dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div.
    """
    
    try:
        if operation=="add":
            result = first_num+second_num
        elif operation=="sub":
            result = first_num-second_num
        elif operation=="mul":
            result = first_num*second_num
        elif operation=="div":
            if second_num==0:
                return {"error": "Division by zero is not allowed"}
            result = first_num/second_num
        else:
            return {'error': f"Unsupported operation '{operation}'"}
        
        return {"first_num":first_num, "second_num":second_num, "operation":operation,
                "result":result}
    except Exception as e:
        return {"error": str(e)}

tools = [search_tool, calculator]
llm_with_tools = model.bind_tools(tools)
        
        
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    
    
def chat_node(state: ChatState):
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {'messages': [response]}

tool_node= ToolNode(tools)

conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")

graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", "chat_node")

# graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)


def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
        
    return list(all_threads)
        

# for message_chunk, metadata in chatbot.stream(
#     {'messages':HumanMessage(content='What is the recipe to make pasta')},
#     config={'configurable':{'thread_id':'thread-1'}},
#     stream_mode='messages'
# ):
#     if message_chunk.content:
#         print(message_chunk.content, end=" ", flush=True)


