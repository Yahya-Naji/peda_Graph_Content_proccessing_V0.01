import streamlit as st
import tempfile
from streamlit_chat import message
from langchain.schema import HumanMessage, AIMessage
from draft1_graphrag import GraphRAG
import fitz  # PyMuPDF library
from langchain.schema import Document

# Page configuration
st.set_page_config(page_title="Pedagogy Knowledge Assistant", page_icon="📘")

# Basic minimalist CSS for a black, white, and beige color theme
css = """
<style>
    body {
        background-color: #f5f5dc; /* Light beige background */
        font-family: 'Georgia', serif;
        color: #333; /* Dark text color */
    }

    /* Main title styling */
    .main-title {
        color: #333;
        font-size: 2.8rem;
        font-weight: bold;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    /* Subtitle styling */
    .subtitle {
        color: #666; /* Muted gray for subtitle */
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 30px;
    }

    /* Container styling */
    .container {
        max-width: 800px;
        margin: auto;
        background-color: #fff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
        margin-top: 20px;
    }

    /* Response bubble styling */
    .response-container {
        background-color: #f0eade; /* Light beige for bubbles */
        padding: 10px;
        border-radius: 12px;
        margin-top: 10px;
    }
    .user-message {
        color: #333;
        font-weight: bold;
    }
    .assistant-message {
        color: #333;
    }

    /* Button styling */
    .stButton>button {
        background-color: #333;
        color: white;
        font-size: 1rem;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #555; /* Slightly darker on hover */
    }

    /* File uploader styling */
    .stFileUploader {
        border: 1px solid #ddd;
        background-color: #f5f5dc;
    }

    /* Chat history styling */
    p {
        font-size: 1rem;
        line-height: 1.5;
    }

</style>
"""

# Apply the CSS styles
st.markdown(css, unsafe_allow_html=True)

# Title and Introduction
st.markdown("<div class='main-title'>Pedagogy Knowledge Assistant</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Your personal assistant for educational resources and insights. Upload your documents and start asking questions!</div>", unsafe_allow_html=True)

# Login page function
def login_page():
    st.title("Welcome to Pedagogy Q&A Portal 📘")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if check_login(username, password):
            st.session_state['logged_in'] = True
            st.success("Login successful")
        else:
            st.error("Invalid username or password")

# Main application function
def main():
    if not st.session_state.get('logged_in'):
        login_page()
        return

    # File uploader section
    st.markdown("<div class='container'><h2>Upload Your Documents</h2></div>", unsafe_allow_html=True)
    portfolio_file = st.file_uploader("Upload your Portfolio PDF here:", type="pdf")
    project_file = st.file_uploader("Upload your Project PDF here:", type="pdf")

    if portfolio_file and project_file:
        with st.spinner("Processing your documents..."):
            with tempfile.NamedTemporaryFile(delete=False) as tmp_portfolio:
                tmp_portfolio.write(portfolio_file.read())
                portfolio_path = tmp_portfolio.name
            
            with tempfile.NamedTemporaryFile(delete=False) as tmp_project:
                tmp_project.write(project_file.read())
                project_path = tmp_project.name

            portfolio_text = load_pdf(portfolio_path)
            project_text = load_pdf(project_path)
            combined_documents = [Document(page_content=portfolio_text), Document(page_content=project_text)]
            st.session_state['documents'] = combined_documents
            st.session_state['ready'] = True
            st.success("Both portfolio and project PDFs have been processed and are ready for queries.")

            if 'graph_rag' not in st.session_state:
                st.session_state['graph_rag'] = GraphRAG()
                st.session_state['graph_rag'].process_documents(st.session_state['documents'])

    # Chat interface
    if st.session_state.get('ready'):
        st.markdown("<div class='container'>", unsafe_allow_html=True)
        if 'generated' not in st.session_state:
            st.session_state['generated'] = ["Welcome! You can now ask any questions regarding the uploaded documents."]
        if 'past' not in st.session_state:
            st.session_state['past'] = ["Hello! How can I assist you with your documents today?"]

        # Text input for queries
        with st.form(key='my_form', clear_on_submit=True):
            query = st.text_input("Enter your query:", key='input')
            submit_button = st.form_submit_button(label='Send')
        if submit_button and query:
            st.session_state['chat_history'].append(HumanMessage(content=query))
            output_raw = st.session_state['graph_rag'].query(query)
            final_answer = output_raw.content if isinstance(output_raw, AIMessage) else output_raw
            st.session_state['chat_history'].append(AIMessage(content=final_answer))
            st.session_state.past.append(query)
            st.session_state.generated.append(final_answer)

        # Display chat history
        for i, chat_message in enumerate(st.session_state['chat_history']):
            if isinstance(chat_message, HumanMessage):
                st.markdown(f"<p class='user-message'><strong>You:</strong> {chat_message.content}</p>", unsafe_allow_html=True)
            elif isinstance(chat_message, AIMessage):
                st.markdown(f"<div class='response-container'>{chat_message.content}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
