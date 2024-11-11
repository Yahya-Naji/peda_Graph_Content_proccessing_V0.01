import streamlit as st
import tempfile
from streamlit_chat import message
from langchain.schema import HumanMessage, AIMessage
from draft1_graphrag import GraphRAG  # Import the main class from draft1_graphrag

# Page configuration
st.set_page_config(page_title="Pedagogy Q&A Assistant", page_icon="📚")

# Custom CSS Styling to Match Pedagogy Publishers' Brand
st.markdown(
    """
    <style>
        /* Main page styling */
        .title {
            font-family: 'Arial', sans-serif;
            color: #AD1457; /* Match Pedagogy branding */
            font-size: 2.5rem;
            font-weight: bold;
        }
        .subtitle {
            font-family: 'Arial', sans-serif;
            color: #6A1B9A;
            font-size: 1.2rem;
        }
        .container {
            padding: 1rem;
            background-color: #FAFAFA; /* Light background for readability */
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            margin-top: 1rem;
        }
        .response-container {
            background-color: #F3E5F5; /* Light purple background for chat bubble */
            padding: 0.8rem;
            border-radius: 12px;
            margin-top: 0.5rem;
            color: #424242;
            font-family: 'Arial', sans-serif;
        }
        .user-message {
            color: #1E88E5;
            font-weight: bold;
        }
        .assistant-message {
            color: #424242;
        }
        /* Button styling */
        .stButton>button {
            background-color: #AD1457;
            color: white;
            font-weight: bold;
            font-size: 1rem;
            border-radius: 8px;
            border: none;
            padding: 0.6rem 1.2rem;
        }
        /* Text input styling */
        .stTextInput>div>div>input {
            border: 2px solid #6A1B9A;
            padding: 0.5rem;
            border-radius: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

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

# Main function for the app
def main():
    # Login management
    if not st.session_state['logged_in']:
        login_page()
        return

    # Title and introduction
    st.markdown("<div class='title'>Chat with PDF using local RagGraph</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Upload a portfolio and a project PDF to start asking questions</div>", unsafe_allow_html=True)

    # File uploader for the PDFs
    portfolio_file = st.file_uploader("Upload your Portfolio PDF here:", type="pdf")
    project_file = st.file_uploader("Upload your Project PDF here:", type="pdf")

    if portfolio_file and project_file:
        with st.spinner("Processing..."):
            # Save the uploaded files to temporary locations
            with tempfile.NamedTemporaryFile(delete=False) as tmp_portfolio:
                tmp_portfolio.write(portfolio_file.read())
                portfolio_path = tmp_portfolio.name
            
            with tempfile.NamedTemporaryFile(delete=False) as tmp_project:
                tmp_project.write(project_file.read())
                project_path = tmp_project.name

            # Load the PDFs using PyPDFLoader (assuming it’s imported in draft1_graphrag)
            portfolio_loader = PyPDFLoader(portfolio_path)
            project_loader = PyPDFLoader(project_path)
            portfolio_documents = portfolio_loader.load()
            project_documents = project_loader.load()
            combined_documents = portfolio_documents + project_documents
            st.session_state['documents'] = combined_documents[:10]  # Limit for testing
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
            st.session_state['past'] = ["Hey!"]

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
