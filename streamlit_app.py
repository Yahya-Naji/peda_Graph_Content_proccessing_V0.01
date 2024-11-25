import streamlit as st
import tempfile
from streamlit_chat import message
from langchain.schema import HumanMessage, AIMessage
from draft1_graphrag import GraphRAG
import fitz  # PyMuPDF library
from langchain.schema import Document  # Import Document class for wrapping text content

# Page configuration
st.set_page_config(page_title="Knowledge Assistant", page_icon="📘")

# Custom CSS Styling for an Enhanced Look
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
            background-color: #e8f5e9;
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
            color: #2e7d32;
            font-family: 'Georgia', serif;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Helper functions
def display_title(organization):
    title = f"{organization} Knowledge Assistant"
    subtitle = "Your personal assistant for educational resources and insights. Upload your documents and start asking questions!"
    st.markdown(f"<div class='main-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitle'>{subtitle}</div>", unsafe_allow_html=True)

def check_login(username, password):
    return username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]

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

def load_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            text += page.get_text()
    return text

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'ready' not in st.session_state:
    st.session_state['ready'] = False

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

if 'documents' not in st.session_state:
    st.session_state['documents'] = []

if 'graph_rag' not in st.session_state:
    st.session_state['graph_rag'] = None

# Main app logic
def main():
    # Login
    if not st.session_state['logged_in']:
        login_page()
        return

    # Dropdown for organization selection
    st.session_state['organization'] = st.selectbox("Select Organization", ["Pedagogy", "Al Fayhaa"])
    display_title(st.session_state['organization'])

    # File uploader for multiple PDFs
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Upload your Project PDFs here:", type="pdf", accept_multiple_files=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_files and st.button("Process Documents"):
        with st.spinner("Processing your documents..."):
            combined_documents = []
            for uploaded_file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    file_path = tmp_file.name
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
        if 'generated' not in st.session_state:
            st.session_state['generated'] = ["Welcome! You can now ask any questions regarding the uploaded documents."]
        if 'past' not in st.session_state:
            st.session_state['past'] = ["Hello! How can I assist you?"]

        # Display chat history
        for i, (user_msg, bot_msg) in enumerate(zip(st.session_state['past'], st.session_state['generated'])):
            message(user_msg, is_user=True, key=f"user_{i}", avatar_style="thumbs")
            message(bot_msg, key=f"bot_{i}", avatar_style="bottts")

        # Chat input box
        with st.form(key="query_form", clear_on_submit=True):
            user_input = st.text_input("Your question:", key="input")
            submit_button = st.form_submit_button(label="Send")

        # Handle user query
        if submit_button and user_input:
            with st.spinner("Generating response..."):
                response = st.session_state['graph_rag'].query(user_input)
                st.session_state['past'].append(user_input)
                st.session_state['generated'].append(response)

if __name__ == "__main__":
    main()
