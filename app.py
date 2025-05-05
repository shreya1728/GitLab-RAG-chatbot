import streamlit as st
import os
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set Streamlit page configuration
st.set_page_config(
    page_title="GitLab Knowledge Bot",
    layout="wide"
)

# Load external CSS
def load_css(file_path="styles.css"):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Constants and configuration
if "GEMINI_API_KEY" in st.secrets:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    # Local development: load from .env file
    from dotenv import load_dotenv
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
VECTOR_DB_PATH = "gitlab_faiss_index"
TEXT_FILE_PATH = "gitlab_scraped.txt"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 10

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Text splitting
def split_text_into_chunks(text_file_path):
    with open(text_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n## ", "\n### ", "\n## ", "\n# ", "\n", " ", ""]
    )

    chunks = text_splitter.split_text(content)
    return chunks

# Vector DB loader or creator
def create_or_load_vector_db():
    # Check if the vector database is already loaded
    if "vector_db" in st.session_state:
        vector_db = st.session_state.vector_db
        st.success("Vector database loaded successfully!")
    else:
        if os.path.exists(VECTOR_DB_PATH):
            with st.spinner("Loading vector database..."):
                vector_db = FAISS.load_local(
                    VECTOR_DB_PATH,
                    GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_API_KEY),
                    allow_dangerous_deserialization=True
                )
                st.session_state.vector_db = vector_db  # Store the loaded vector db in session state
                st.success("Vector database loaded successfully!")
        else:
            with st.spinner("Creating vector database from text file..."):
                if not os.path.exists(TEXT_FILE_PATH):
                    st.error(f"Text file not found: {TEXT_FILE_PATH}")
                    return None

                chunks = split_text_into_chunks(TEXT_FILE_PATH)
                st.info(f"Split text into {len(chunks)} chunks")

                embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001",
                    google_api_key=GEMINI_API_KEY
                )
                vector_db = FAISS.from_texts(chunks, embeddings)
                vector_db.save_local(VECTOR_DB_PATH)
                st.session_state.vector_db = vector_db  # Store the newly created vector db in session state
                st.success("Vector database created successfully!")

    return vector_db

# Main RAG function with guardrails and follow-up call
def generate_response(query, vector_db, chat_history):
    genai.configure(api_key=GEMINI_API_KEY)

    forbidden_patterns = ["hack", "exploit", "bypass", "crack", "illegal", "porn", "nsfw", "weapon", "violence"]
    if any(re.search(rf"\b{pattern}\b", query.lower()) for pattern in forbidden_patterns):
        return "⚠️ I'm not able to help with that request as it goes against ethical usage policies."

    results = vector_db.similarity_search(query, k=TOP_K_RESULTS)
    context_text = "\n\n".join([doc.page_content for doc in results])

    history_text = ""
    if chat_history:
        for msg in chat_history:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"

    prompt = f"""
You are a knowledgeable assistant that specializes in GitLab documentation.
Answer the user's question based on the provided context from GitLab documentation.
Give detailed and elaborate answers. Try to explain your answers. Search the context thoroughly for the question asked.
If the context doesn't contain the relevant information, get the information from the gitlab website.

CONTEXT:
{context_text}

CHAT HISTORY:
{history_text}

USER QUESTION: {query}

Your response should be informative, accurate, and based only on the provided context. 
"""

    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)

    return response.text

# Suggest follow-up questions
def suggest_follow_ups(query, vector_db):
    genai.configure(api_key=GEMINI_API_KEY)

    followup_prompt = f"""
Given the user's question: "{query}",
suggest 2-3 relevant follow-up questions that could help them better understand GitLab concepts or related features.

Format:
- Follow-up 1
- Follow-up 2
- Follow-up 3
"""

    model = genai.GenerativeModel('gemini-2.0-flash')
    followups = model.generate_content(followup_prompt)
    return followups.text

# Display chat message
def format_chat_message(message, is_user=False):
    if is_user:
        st.markdown(
            f"""
            <div class="user-message">
                <div class="user-message-content">
                    <p>{message}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="bot-message">
                <div class="bot-message-content">
                    <p>{message}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# Main app
def main():
    st.title("GitLab Knowledge Bot 💻")
    st.markdown("Ask questions about GitLab's handbook and direction documents, and get answers based on the scraped content.")

    # Sidebar
    st.sidebar.title("Configuration")

    if not GEMINI_API_KEY:
        st.warning("Please Enter a valid Gemini API key")
        return

    try:
        vector_db = create_or_load_vector_db()
        if vector_db is None:
            return
    except Exception as e:
        st.error(f"Error initializing vector database: {str(e)}")
        return
    if len(st.session_state.messages) == 0:
        st.markdown("### 💡 Suggested Questions")
        st.markdown("""
                - What are the six core values of GitLab?
                - How does GitLab reinforce values?
                - Can you tell me about GitLab's CI/CD?
                - What are the hiring practices of GitLab?
                """)


    # Chat History
    for message in st.session_state.messages:
        format_chat_message(message["content"], message["role"] == "user")

    # Chat input
    user_query = st.chat_input("Ask something about GitLab...")
    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        format_chat_message(user_query, True)

        with st.spinner("Thinking..."):
            try:
                response = generate_response(user_query, vector_db, st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": response})
                format_chat_message(response)

                # Suggested follow-ups
                followups = suggest_follow_ups(user_query, vector_db)
                with st.expander("💡 Suggested Follow-Up Questions"):
                    st.markdown(followups)

            except Exception as e:
                st.error(f"Error generating response: {str(e)}")

    if st.sidebar.button("Clear Chat History"):
        st.session_state.messages = []
        st.experimental_rerun()

    # Data source info
    st.sidebar.markdown("### About the Data")
    st.sidebar.markdown("""
This chatbot uses content scraped from:
- GitLab Handbook (https://handbook.gitlab.com/)
- GitLab Direction (https://about.gitlab.com/direction/)

The content is chunked, embedded, and stored in a FAISS vector database for efficient retrieval.
""")
    
   
    st.sidebar.markdown("---")
    # Ethical Use Info
    st.sidebar.markdown("### ⚠️ Ethical Use")
    st.sidebar.markdown("""
This assistant is designed for educational and documentation-related queries **within GitLab's scope**.

❌ Avoid using it for:
- Hacking or exploitation guidance  
- NSFW or violent content  
- Illegal or unethical advice

✅ Stay within professional and constructive queries.
""")

if __name__ == "__main__":
    main()
