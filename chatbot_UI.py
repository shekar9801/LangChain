import streamlit as st
from chatbot_using_langgraph import  chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage, AIMessage
import uuid

def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id
    
def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []
    
def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)
        
        
def load_conversation(thread_id):
    return chatbot.get_state(config={'configurable': {'thread_id':thread_id}}).values['messages']
    
    
    
st.set_page_config(layout="centered")

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
    
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()
    
add_thread(st.session_state['thread_id'])


st.sidebar.title("LangGraph Chatbot")
if st.sidebar.button('New Chat', use_container_width=True):
    reset_chat()
    
st.sidebar.header('History')

for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id']=thread_id
        messages = load_conversation(thread_id)
        
        temp_messages=[]
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role='user'
            else:
                role='assistant'
            temp_messages.append({'role':role, 'content':msg.content})
        st.session_state['message_history'] = temp_messages
                



for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])


CONFIG = {'configurable': {'thread_id':st.session_state['thread_id']}}

    
user_input = st.chat_input("Type here")

if user_input:
    
    st.session_state['message_history'].append({'role':'user', 'content':user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
        
    # with st.chat_message("assistant"):
    #     ai_message = st.write_stream(
    #        message_chunk.content for message_chunk, metadata in chatbot.stream(
    #              {'messages':HumanMessage(content=user_input)},
    #             config=CONFIG,
    #             stream_mode='messages'
    #         )
    #     )
        
        
    with st.chat_message("assistant"):
        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            ):
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content
                    
        ai_message = st.write_stream(ai_only_stream())
            
        
    st.session_state['message_history'].append({'role':'assistant', 'content':ai_message})
        
