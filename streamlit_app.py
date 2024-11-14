import streamlit as st
import tempfile
from streamlit_chat import message
from langchain.schema import HumanMessage, AIMessage
from draft1_graphrag import GraphRAG
import fitz  # PyMuPDF library
from langchain.schema import Document

# Page configuration
st.set_page_config(page_title="Knowledge Assistant", page_icon="📘")

# Custom CSS Styling for an Elegant Look
st.markdown(
    """
    <style>
        /* Add custom CSS styling here */
    </style>
    """,
    unsafe_allow_html=True
)

# Dropdown selection for organization
organization = st.selectbox("Select Organization", ["Pedagogy", "Al Fayhaa"])

# Display organization-specific title and introduction
if organization == "Pedagogy":
    st.markdown("<div class='main-title'>Pedagogy Knowledge Assistant</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Your personal assistant for educational resources and insights. Upload your documents and start asking questions!</div>", unsafe_allow_html=True)
elif organization == "Al Fayhaa":
    st.markdown("<div class='main-title'>Al Fayhaa Knowledge Assistant</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='subtitle'>Al-Fayhaa Association: Empowering Communities Through Education and Advocacy. Upload documents and explore our initiatives.</div>", 
        unsafe_allow_html=True
    )
    st.markdown(
        """
        **About Al Fayhaa Association**  
        Al-Fayhaa Association is a non-profit organization in Lebanon, established in 1999, dedicated to building underprivileged communities through education, protection, and advocacy programs, ensuring equal and value-added services for all. With no political or sectarian orientation, the organization focuses on neutrality and inclusivity.

        **Mission**  
        Al Fayhaa strives to build competent citizens who value education by investing in curriculum development, protection programs, and child advocacy. Their goal is to maximize access to quality education and protection for children and youth across the region.

        **Contact Information**  
        - **Location**: -1 Floor, City Complex, Riad el Solh Road, Tripoli, Lebanon
        - **Phone**: +961 6 44 66 81
        - **Email**: info@al-fayhaa.org
        - **Website**: [Al Fayhaa](http://www.al-fayhaa.org)
        """,
        unsafe_allow_html=True
    )

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

# Initialize session state
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

    # File uploader for multiple project folders (PDFs)
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Upload your Project PDFs here:", type="pdf", accept_multiple_files=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Proceed button to process files
    if uploaded_files and st.button("Proceed"):
        with st.spinner("Processing your documents..."):
            combined_documents = []
            for uploaded_file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    file_path = tmp_file.name
                
                # Load text from each PDF and wrap in LangChain's Document format
                file_text = load_pdf(file_path)
                combined_documents.append(Document(page_content=file_text))
            
            # Store documents in session state
            st.session_state['documents'] = combined_documents
            st.session_state['ready'] = True
            st.success("All project PDFs have been processed and are ready for queries.")

            # Initialize GraphRAG and store it in session state
            if 'graph_rag' not in st.session_state:
                st.session_state['graph_rag'] = GraphRAG()
                st.session_state['graph_rag'].process_documents(st.session_state['documents'])

    st.divider()

    # Chat interface and document query functionality
    if st.session_state['ready']:
        if 'generated' not in st.session_state:
            st.session_state['generated'] = ["Welcome! You can now ask any questions regarding the uploaded documents."]
        if 'past' not in st.session_state:
            st.session_state['past'] = ["Hello! How can I assist you with your documents today?"]

        response_container = st.container()
        container = st.container()

        with container:
            with st.form(key='my_form', clear_on_submit=True):
                query = st.text_input("Enter your query:", key='input')
                submit_button = st.form_submit_button(label='Send')
            if submit_button and query:
                st.session_state['chat_history'].append(HumanMessage(content=query))
                context = f"""
                You are a Q&A assistant for the {organization} portal. When the user mentions "project," "uploaded project," or "PDF,"
                assume they are most likely referring to the content of the most recently uploaded document unless specified.
                Provide information from the uploaded documents first.
                """
                full_query = f"{context}\n{query}"

                output_raw = st.session_state['graph_rag'].query(full_query)
                final_answer = output_raw.content if isinstance(output_raw, AIMessage) else output_raw
                
                st.session_state['chat_history'].append(AIMessage(content=final_answer))
                st.session_state.past.append(query)
                st.session_state.generated.append(final_answer)

        if st.session_state['generated']:
            with response_container:
                for i, chat_message in enumerate(st.session_state['chat_history']):
                    if isinstance(chat_message, HumanMessage):
                        st.markdown(f"<div class='user-message'>**You:** {chat_message.content}</div>", unsafe_allow_html=True)
                    elif isinstance(chat_message, AIMessage):
                        st.markdown(f"<div class='response-container'><p class='assistant-message'>{chat_message.content}</p></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
