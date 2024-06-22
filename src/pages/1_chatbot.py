import os
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from langchain.document_loaders import AsyncHtmlLoader
from langchain.document_transformers import Html2TextTransformer



load_dotenv()
URLS = ["https://www.webmd.com/drugs/2/drug-172941/magnesium-l-threonate-oral/details", 
        "https://www.webmd.com/vitamins/ai/ingredientmono-1126/berberine",
        "https://www.mayoclinic.org/drugs-supplements-vitamin-d/art-20363792"
       ]

def get_vectorstore_from_url():
    if os.path.isdir("./chroma_db"):
        return Chroma(persist_directory="./chroma_db", embedding_function=OpenAIEmbeddings())

        
    loader = AsyncHtmlLoader(URLS)
    docs = loader.load()

    html2text_transformer = Html2TextTransformer()
    docs_transformed = html2text_transformer.transform_documents(docs)
    text_splitter = RecursiveCharacterTextSplitter()
    document_chunks = text_splitter.split_documents(docs_transformed)
    
    
    # create a vectorstore from the chunks
    vector_store = Chroma.from_documents(document_chunks, OpenAIEmbeddings(), persist_directory="./chroma_db")

    return vector_store

def get_context_retriever_chain(vector_store):
    llm = ChatOpenAI()
    
    retriever = vector_store.as_retriever()
    
    prompt = ChatPromptTemplate.from_messages([
      MessagesPlaceholder(variable_name="chat_history"),
      ("user", "{input}"),
      ("user", "Given the above conversation, generate a search query to look up in order to get information relevant to the conversation")
    ])
    
    retriever_chain = create_history_aware_retriever(llm, retriever, prompt)
    
    return retriever_chain
    
def get_conversational_rag_chain(retriever_chain): 
    
    llm = ChatOpenAI()
    
    prompt = ChatPromptTemplate.from_messages([
      ("system", get_prompt_prefix() + "Answer the user's questions based on the below context:\n\n{context}"),
      MessagesPlaceholder(variable_name="chat_history"),
      ("user", "{input}"),
    ])
    
    stuff_documents_chain = create_stuff_documents_chain(llm,prompt)
    
    return create_retrieval_chain(retriever_chain, stuff_documents_chain)

def get_response(user_input):
    retriever_chain = get_context_retriever_chain(st.session_state.vector_store)
    conversation_rag_chain = get_conversational_rag_chain(retriever_chain)
    
    response = conversation_rag_chain.invoke({
        "chat_history": st.session_state.chat_history,
        "input": user_input
    })
    
    return response['answer']

def get_prompt_prefix():
    prefix = f"Help the user personalize their supplement routine. Here's an overview of the user's profile:\n" \
             f"Name: {st.session_state['name']}" \
             f"Age: {st.session_state['age']}" \
             f"Weight: {st.session_state['weight']} lbs" \
             f"\n\n"    
    return prefix

# app config
st.set_page_config(page_title="Supplement Bot", page_icon="🤖")
st.title("Supplement Bot")

    # Step 1: Form to collect user information
if 'form_submitted' not in st.session_state:
    with st.form("user_form"):
        st.subheader("Please fill out your information")
        name = st.text_input("Name")
        age = st.text_input("Age")
        weight = st.text_input("Weight (lbs)")
        submit = st.form_submit_button("Submit")

        if submit:
            if name and age:
                st.session_state['name'] = name
                st.session_state['age'] = age
                st.session_state['weight'] = weight
                st.session_state['form_submitted'] = True
            else:
                st.error("Please fill out all fields")
else:
    # session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            AIMessage(content=f"Hello {st.session_state['name']}, I am a bot. How can I help you?"),
        ]
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = get_vectorstore_from_url()    

    # user input
    user_query = st.chat_input("Type your message here...")
    if user_query is not None and user_query != "":
        response = get_response(user_query)
        st.session_state.chat_history.append(HumanMessage(content=user_query))
        st.session_state.chat_history.append(AIMessage(content=response))
        
        

    # conversation
    for message in st.session_state.chat_history:
        if isinstance(message, AIMessage):
            with st.chat_message("AI"):
                st.write(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message("Human"):
                st.write(message.content)