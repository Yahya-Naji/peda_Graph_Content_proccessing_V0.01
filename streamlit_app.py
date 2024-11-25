import streamlit as st
import tempfile
from streamlit_chat import message
from langchain.schema import HumanMessage, AIMessage
from draft1_graphrag import GraphRAG  # Import the main class from draft1_graphrag
import fitz  # PyMuPDF library
from langchain.schema import Document  # Import Document class for wrapping text content

# Page configuration
st.set_page_config(page_title="Knowledge Assistant", page_icon="📘")

# Custom CSS Styling for an Elegant Look
st.markdown(
    """
    <style>
        .main-title {
            font-family: 'Georgia', serif;
            color: #4E2A84;
            font-size: 2.8rem;
            font-weight: bold;
            text-align: center;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .subtitle {
            font-family: 'Georgia', serif;
            color: #7A3E93;
            font-size: 1.2rem;
            text-align: center;
            margin-bottom: 30px;
        }
        .container {
            max-width: 800px;
            margin: auto;
            background-color: #f9f7fc;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
            margin-top: 20px;
        }
        .response-container {
            background-color: #e0d7f8;
            padding: 10px;
            border-radius: 12px;
            margin-top: 10px;
            color: #333333;
            font-family: 'Georgia', serif;
        }
        .user-message {
            color: #4E2A84;
            font-weight: bold;
            font-family: 'Georgia', serif;
        }
        .assistant-message {
            color: #333333;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'ready' not in st.session_state:
    st.session_state['ready'] = False

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

if 'organization' not in st.session_state:
    st.session_state['organization'] = "Pedagogy"

if 'graph_rag' not in st.session_state:
    st.session_state['graph_rag'] = None

if 'documents' not in st.session_state:
    st.session_state['documents'] = []

# Function to check login
def check_login(username, password):
    return username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]

# Login page function
def login_page():
    st.title("Welcome to Knowledge Q&A Portal 📘")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if check_login(username, password):
            st.session_state['logged_in'] = True
            st.success("Login successful")
        else:
            st.error("Invalid username or password")

# Function to load PDF text using PyMuPDF
def load_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            text += page.get_text()
    return text

# Main function
def main():
    if not st.session_state['logged_in']:
        login_page()
        return

    # Dropdown for organization
    st.session_state['organization'] = st.selectbox("Select Organization", ["Pedagogy", "Al Fayhaa"])
    st.markdown(f"<div class='main-title'>{st.session_state['organization']} Knowledge Assistant</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='subtitle'>Your personal assistant for educational resources and insights. Upload your documents and start asking questions!</div>",
        unsafe_allow_html=True,
    )

    # File uploader
    uploaded_files = st.file_uploader("Upload your Project PDFs here:", type="pdf", accept_multiple_files=True)

    # Process documents
    if uploaded_files and st.button("Process Documents"):
        with st.spinner("Processing your documents..."):
            combined_documents = []
            for uploaded_file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    file_path = tmp_file.name
                # Load text from each PDF
                file_text = load_pdf(file_path)
                combined_documents.append(Document(page_content=file_text))
            st.session_state['documents'] = combined_documents
            st.session_state['graph_rag'] = GraphRAG()
            st.session_state['graph_rag'].process_documents(combined_documents)
            st.session_state['ready'] = True
            st.success("Documents processed successfully! You can now ask questions.")

    st.divider()

    # Chat interface
    if st.session_state['ready']:
        with st.container():
            with st.form(key="query_form", clear_on_submit=True):
                user_query = st.text_input("Enter your query:")
                submit_button = st.form_submit_button(label="Send")
            
            if submit_button and user_query:
                # Process user query
                with st.spinner("Generating response..."):
                    response = st.session_state['graph_rag'].query(user_query)
                    st.session_state['chat_history'].append((user_query, response))

        # Display chat history
        for i, (user_message, bot_message) in enumerate(st.session_state['chat_history']):
            message(user_message, is_user=True, key=f"user_{i}")
            message(bot_message, key=f"bot_{i}")

if __name__ == "__main__":
    main()
