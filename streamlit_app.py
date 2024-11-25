import streamlit as st
import tempfile
from streamlit_chat import message
from langchain.schema import HumanMessage, AIMessage
from draft1_graphrag import GraphRAG
import fitz  # PyMuPDF library
from langchain.schema import Document  # Import Document class for wrapping text content

# Page configuration
st.set_page_config(page_title="Knowledge Assistant", page_icon="📘")

# CSS for styling
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

# Display title and subtitle
def display_title(organization):
    title = f"{organization} Knowledge Assistant"
    subtitle = "Your personal assistant for educational resources and insights. Upload your documents and start asking questions!"
    st.markdown(f"<div class='main-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitle'>{subtitle}</div>", unsafe_allow_html=True)

# Login verification
def check_login(username, password):
    return username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]

# Load PDF text
def load_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page_num in range(pdf.page_count):
            text += pdf[page_num].get_text()
    return text

# Initialize session state
for key in ["logged_in", "ready", "chat_history", "documents", "graph_rag", "organization"]:
    if key not in st.session_state:
        st.session_state[key] = False if key in ["logged_in", "ready"] else []

def main():
    # Login logic
    if not st.session_state['logged_in']:
        st.title("Welcome to Knowledge Q&A Portal 📘")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if check_login(username, password):
                st.session_state['logged_in'] = True
                st.success("Login successful")
            else:
                st.error("Invalid username or password")
        return

    # Organization selection
    st.session_state['organization'] = st.selectbox("Select Organization", ["Pedagogy", "Al Fayhaa"])
    display_title(st.session_state['organization'])

    # File uploader for PDFs
    uploaded_files = st.file_uploader("Upload your Project PDFs here:", type="pdf", accept_multiple_files=True)
    if uploaded_files and st.button("Process Documents"):
        with st.spinner("Processing your documents..."):
            combined_text = ""  # Initialize an empty string to store combined text

            # Extract text from each PDF and combine them
            for file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    tmp_file.write(file.read())
                    file_path = tmp_file.name
                
                # Extract text from the PDF
                file_text = load_pdf(file_path)
                combined_text += file_text + "\n"  # Append the text with a newline separator

            # Create a single Document object from the combined text
            combined_document = Document(page_content=combined_text)

            # Store the combined document in session state
            st.session_state['documents'] = [combined_document]

            # Initialize and process GraphRAG
            if 'graph_rag' not in st.session_state:
                st.session_state['graph_rag'] = GraphRAG()
            st.session_state['graph_rag'].process_documents([combined_document])  # Pass the combined document
            st.session_state['ready'] = True
            st.success("Documents processed successfully! You can now ask questions.")

    # Divider for UI separation
    st.divider()

    # Chat interface
    if st.session_state['ready']:
        # Initialize chat history if not present
        if 'chat_history' not in st.session_state:
            st.session_state['chat_history'] = []

        # Display previous chat messages
        for i, (user_msg, bot_msg) in enumerate(st.session_state['chat_history']):
            message(user_msg, is_user=True, key=f"user_{i}")
            message(bot_msg, key=f"bot_{i}")

        # Form for user to input questions
        with st.form(key="query_form"):
            user_query = st.text_input("Ask your question:")
            if st.form_submit_button("Send"):
                # Query the GraphRAG and get a response
                response = st.session_state['graph_rag'].query(user_query)

                # Extract the readable content from the response
                response_str = response.content if isinstance(response, AIMessage) else str(response)

                # Append user query and response to chat history
                st.session_state['chat_history'].append((f"**You:** {user_query}", f"**Assistant:** {response_str}"))

                # Display chat messages
                message(f"**You:** {user_query}", is_user=True)
                message(f"**Assistant:** {response_str}")

if __name__ == "__main__":
    main()
