# GitLab Knowledge Bot 🤖
An AI-powered chatbot that provides detailed answers based on GitLab's official documentation. It leverages Retrieval-Augmented Generation (RAG) to fetch relevant information from GitLab's Handbook and Direction pages, ensuring accurate and context-rich responses.

## 🚀 Features

- **Streamlit Interface**: User-friendly web interface for seamless interactions.

- **Web Scraper**: Custom scraper to extract content from GitLab's Handbook and Direction pages.

- **Text Chunking**: Splits large texts into manageable chunks for efficient processing.

- **Vector Database**: Stores embeddings using FAISS for quick similarity searches.

- **Gemini API Integration**: Utilizes Google's Gemini API for generating responses.

- **Contextual Responses**: Provides answers based on retrieved context, ensuring relevance.

- **Follow-up Suggestions**: Suggests related questions to enhance user understanding.

- **Ethical Guardrails**: Filters out inappropriate or unethical queries.


## 🛠️ Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/gitlab-knowledge-bot.git
cd gitlab-knowledge-bot
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a .env file in the root directory and add your GEMINI API key:
```bash
GEMINI_API_KEY=your_gemini_api_key
```

### 5. Scrape GitLab Documentation
Run the scraper to extract content from GitLab's Handbook and Direction pages:

```bash
python scraper.py
```

### 6. Launch the Streamlit App
```bash
streamlit run app.py
```
The application will open in your default web browser.

🧠 How It Works
Data Extraction: scraper.py crawls specified GitLab URLs, extracting headings, paragraphs, and list items, saving them to gitlab_scraped.txt.

Text Chunking: The content is split into chunks using RecursiveCharacterTextSplitter for better embedding.

Embedding Generation: Each chunk is converted into a vector using Google's Generative AI Embeddings.

Vector Storage: Embeddings are stored in a FAISS vector database for efficient similarity searches.

User Interaction: Users input queries via the Streamlit interface.

Context Retrieval: The system retrieves top-k similar chunks from the vector database.

Response Generation: A prompt combining the user's question and retrieved context is sent to the Gemini API, which generates a detailed response.

Follow-up Suggestions: The system suggests related questions to guide further exploration.

⚙️ Configuration
- Chunk Size: 1000 characters

- Chunk Overlap: 200 characters

- Top-K Results: 10

- Embedding Model: models/embedding-001

- Generative Model: gemini-2.0-flash

- These parameters can be adjusted in app.py as needed.
