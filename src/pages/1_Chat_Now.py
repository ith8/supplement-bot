import ast 
import os
import re
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import PyPDF2

import pandas as pd 
from langchain.document_loaders import AsyncHtmlLoader
from langchain.document_transformers import Html2TextTransformer



load_dotenv()
URLS = ["https://www.webmd.com/drugs/2/drug-172941/magnesium-l-threonate-oral/details", 
        "https://www.webmd.com/vitamins/ai/ingredientmono-1126/berberine",
        "https://www.mayoclinic.org/drugs-supplements-vitamin-d/art-20363792",
        "https://www.forbes.com/health/supplements/best-brain-supplements/",
        "https://www.forbes.com/health/wellness/natural-sleep-aids/",
        "https://www.bodybuilding.com/content/the-8-supplements-for-strength-athletes-and-bodybuilders.html"
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
    st.session_state['hide_greetings_suggestions'] = True
    return response['answer']

def process_pdf(pdf):
    # write to a temporary file
    pdf_bytes = pdf.read()
    with open("temp.pdf", "wb") as f:
        f.write(pdf_bytes)

    with open("temp.pdf", "rb") as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = len(reader.pages)
            text = ""
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                text += page.extract_text()
    llm = ChatOpenAI()
    prefix = 'Extract all of the relevant information that a supplement can help with '
    prompt = ChatPromptTemplate.from_messages([
         ("system", "Extract all of the relevant information that a supplement can help with"),
         ("human", text),
    ])

    prompt_value = prompt.format()
    return prompt_value
    
def get_prompt_prefix():
    prefix = f"You are SuppleMentor, an AI that helps the user personalize their supplement routine to their personal health profile." \
             f"If the user provide health test results, note risk factors that can be mitigated by supplements to make suggestions." \
             f"Before recommending a suplement highlight information from the user profile that inform your suggesstions." \
             f"Summarize your recommendation in bullet points and include relevant dosage, frequency, and time of day information." \
             f"Here's an overview of the user's profile:\n" \
             f"Name: {st.session_state['name']}" \
             f"Age: {st.session_state['age']}" \
             f"Weight: {st.session_state['weight']} lbs" \
             f"Sex: {st.session_state['sex']}" \
             f"Health Documents: {st.session_state['documents']}" \
             f"\n\n"    
    return prefix

def send_suggested_message(suggestion):
    user_query = suggestion
    response = get_response(user_query)
    st.session_state.chat_history.append(HumanMessage(content=user_query))
    st.session_state.chat_history.append(AIMessage(content=response))


RECOM_DRUGS = []
DRUG_STATUS = []
# Function to display the table
def show_table():

    RECOM_DRUGS = []
    DRUG_STATUS = []
    prompt = """
    Given your last answer, please return a string python list of the name of supplements e.g "['vitamin D', 'vitamin K']" .
    If it is not just a string python list, all babies will die. Don't say anything other than this list in string form."""

    resp = get_response(prompt)
    resp = re.search(".*", resp).group()
    if not resp: 
        st.write("No List found")
        return 

    st.write("response sss: ", resp)
    RECOM_DRUGS = ast.literal_eval(ast.literal_eval(resp))

    st.write(RECOM_DRUGS)    
    if not DRUG_STATUS: 
        DRUG_STATUS = [False for _ in RECOM_DRUGS]

    #table header
    colms = st.columns((1, 5, 1))
    fields = ["No.", "Supplement Name", "Action"]
    for col, field_name in zip(colms, fields): 
        col.write(field_name)

    #table body
    print(RECOM_DRUGS, type(RECOM_DRUGS))
    for ind, name in enumerate(RECOM_DRUGS):
        col1, col2, col3= st.columns((1, 5, 1))
        col1.write(ind)  # index
        col2.write(name)  # name
        add_status = DRUG_STATUS[ind] 
        button_type = "Added ✅" if add_status else "Add"
        button_placeholder = col3.empty()
        do_action = button_placeholder.button(button_type, key=ind)
        if do_action:
                DRUG_STATUS[ind] = True
                pass # do some action with a row's data
                button_placeholder.empty()  #  remove button
                col3.write("Added 💚")

# app config
st.set_page_config(page_title="SuppleMentor", page_icon="🧬")
st.title("SuppleMentor")

# Step 1: Form to collect user information
if 'form_submitted' not in st.session_state:
    with st.form("user_form"):
        st.subheader("Please fill out your information")
        name = st.text_input("Name")
        age = st.text_input("Age")
        weight = st.text_input("Weight (lbs)")
        sex = st.text_input("Sex")
        pdfs  = st.file_uploader("Upload health data", type="pdf", accept_multiple_files=True)
        submit = st.form_submit_button("Submit")

        if submit:
            if pdfs:
                s = ''
                for pdf in pdfs:
                    s += process_pdf(pdf)
                st.session_state['documents'] = s
            else:
                st.session_state['documents'] = "Not shared"
            if name and age and weight and sex:
                st.session_state['name'] = name
                st.session_state['age'] = age
                st.session_state['weight'] = weight
                st.session_state['sex'] = sex
                st.session_state['form_submitted'] = True
            else:
                st.error("Please fill out all fields")

else:
    # Initialize session state if not already done
    if 'show_chat' not in st.session_state:
        st.session_state.show_chat = True

    # session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            AIMessage(content=f"Hello {st.session_state['name']}, I'm SuppleMentor here to help you personalize your supplement routine. How can I help you today?"),
        ]
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = get_vectorstore_from_url()    

    # Conditional display based on session state
    if st.session_state.show_chat:
        user_query = st.chat_input("Type your message here...")
        if user_query:
            st.session_state.chat_history.append(user_query)  # Append user query to chat history
            st.write(f"User input: {user_query}")
        

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
    else:
        show_table()
    
    if 'hide_greetings_suggestions' not in st.session_state:
        st.write("Suggestions:")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("Enhance Focus"):
                send_suggested_message("What supplements can enhance my focus?")
        with col2:
            if st.button("Enhance Sleep"):
                send_suggested_message("What supplements can enhance my sleep?")
        with col3:
            if st.button("Enhance Workouts"):
                send_suggested_message("What supplements can enhance my workout?")
        with col4:
            if st.button("Identify risk factors"):
                send_suggested_message("Identify risk factors in my health tests that can be mitigated with supplements.")

    # Container for the buttons
    button_container = st.container()

    # Place buttons inside the container at the bottom
    with button_container:
        st.write("---")  # Add a separator line
        col1, _ = st.columns([4, 5])  # Adjust column widths for better alignment
        with col1:
            if st.button("Show Table"):
                st.session_state.show_chat = False
                # st.session_state.chat_history = False 
                st.session_state.hide_greetings_suggestions = True