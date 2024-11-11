import streamlit as st
import tempfile
from streamlit_chat import message
from langchain.schema import HumanMessage, AIMessage
from draft1_graphrag import GraphRAG  # Import the main class from draft1_graphrag
import fitz  # PyMuPDF library

# Page configuration
st.set_page_config(page_title="Pedagogy Knowledge Assistant", page_icon="📘")

# Custom CSS Styling for an Elegant Look
st.markdown(
    """
    <style>
        /* Main title styling */
        .main-title {
            font-family: 'Georgia', serif;
            color: #4E2A84; /* Dark purple for a classic feel */
            font-size: 2.8rem;
            font-weight: bold;
            text-align: center;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        /* Subtitle styling */
        .subtitle {
            font-family: 'Georgia', serif;
            color: #7A3E93; /* Muted purple for elegance */
            font-size: 1.2rem;
            text-align: center;
            margin-bottom: 30px;
        }
        /* Container styling for sections */
        .container {
            max-width: 800px;
            margin: auto;
            background-color: #f9f7fc; /* Soft background for readability */
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
            margin-top: 20px;
        }
        /* Styling for response bubbles */
        .response-container {
            background-color: #e0d7f8; /* Light purple background */
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
        /* Button styling */
        .stButton>button {
            background-color: #4E2A84;
            color: white;
            font-weight: bold;
            font-size: 1rem;
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            border: none;
            transition: background-color 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #7A3E93; /* Slight hover effect */
        }
        /* Text input styling */
        .stTextInput>div>div>input {
            border: 2px solid #7A3E93;
            padding: 0.5rem;
            border-radius: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Title and Introduction
st.markdown("<div class='main-title'>Pedagogy Knowledge Assistant</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Your personal assistant for educational resources and insights. Upload your documents and start asking questions!</div>", unsafe_allow_html=True)

# Function to check login
def check_login(username, password):
    return username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]

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

# Initialize session state for the app
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'ready' not in st.session_state:
    st.session_state['ready'] = False

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# Function to load PDF text using PyMuPDF
def load_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            text += page.get_text()
    return text

# Main function for the app
def main():
    # Login management
    if not st.session_state['logged_in']:
        login_page()
        return

    # File uploader for the PDFs
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    portfolio_file = st.file_uploader("Upload your Portfolio PDF here:", type="pdf")
    project_file = st.file_uploader("Upload your Project PDF here:", type="pdf")
    st.markdown("</div>", unsafe_allow_html=True)

    if portfolio_file and project_file:
        with st.spinner("Processing your documents..."):
            # Save the uploaded files to temporary locations
            with tempfile.NamedTemporaryFile(delete=False) as tmp_portfolio:
                tmp_portfolio.write(portfolio_file.read())
                portfolio_path = tmp_portfolio.name
            
            with tempfile.NamedTemporaryFile(delete=False) as tmp_project:
                tmp_project.write(project_file.read())
                project_path = tmp_project.name

            # Load text from the PDFs
            portfolio_text = load_pdf(portfolio_path)
            project_text = load_pdf(project_path)
            combined_documents = [portfolio_text, project_text]
            st.session_state['documents'] = combined_documents  # Store the text in session
            st.session_state['ready'] = True
            st.success("Both portfolio and project PDFs have been processed and are ready for queries.")

            # Initialize GraphRAG and store it in session state after processing documents
            if 'graph_rag' not in st.session_state:
                st.session_state['graph_rag'] = GraphRAG()
                st.session_state['graph_rag'].process_documents(st.session_state['documents'])

    st.divider()

    # Check if the document is ready for questions
    if st.session_state['ready']:
        if 'generated' not in st.session_state:
            st.session_state['generated'] = ["Welcome! You can now ask any questions regarding the uploaded documents."]
        if 'past' not in st.session_state:
            st.session_state['past'] = ["Hello! How can I assist you with your documents today?"]

        # Chat container
        response_container = st.container()
        container = st.container()

        # Text input for queries
        with container:
            with st.form(key='my_form', clear_on_submit=True):
                query = st.text_input("Enter your query:", key='input')
                submit_button = st.form_submit_button(label='Send')
            if submit_button and query:
                # Add the human message to the chat history
                st.session_state['chat_history'].append(HumanMessage(content=query))

                # Combine context with the query
                context = """
                You are a Q&A assistant for the Pedagogy portal. When the user mentions "project," "uploaded project," or "PDF,"
                assume they are most likely referring to the content of the most recently uploaded document unless they specify otherwise.
                Provide information from the uploaded documents first, focusing on their specific content, and clarify if needed.
                """
                full_query = f"{context}\n{query}"

                # Process the query with the stored GraphRAG instance
                output_raw = st.session_state['graph_rag'].query(full_query)
                
                # Extract the content from the output to avoid metadata
                final_answer = output_raw.content if isinstance(output_raw, AIMessage) else output_raw
                
                # Add the AI response to the chat history
                st.session_state['chat_history'].append(AIMessage(content=final_answer))

                # Append query and output for display
                st.session_state.past.append(query)
                st.session_state.generated.append(final_answer)

        # Display chat history
        if st.session_state['generated']:
            with response_container:
                for i, chat_message in enumerate(st.session_state['chat_history']):
                    if isinstance(chat_message, HumanMessage):
                        st.markdown(f"<div class='user-message'>**You:** {chat_message.content}</div>", unsafe_allow_html=True)
                    elif isinstance(chat_message, AIMessage):
                        st.markdown(
                            f"""
                            <div class="response-container">
                                <p class="assistant-message">{chat_message.content}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

if __name__ == "__main__":
    main()
