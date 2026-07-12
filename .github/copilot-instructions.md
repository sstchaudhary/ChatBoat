# GitHub Copilot Instructions — Document-Based RAG Chatbot

## Project Overview
This is a **Retrieval-Augmented Generation (RAG) chatbot** that answers questions ONLY from user-uploaded documents (PDF, DOCX, TXT). It never uses outside knowledge.

**Stack:**
- **Backend**: Django + Django REST Framework
- **Frontend**: React (Vite) + Axios + react-dropzone
- **LLM**: Ollama (local) running `llama3.2`
- **Embeddings**: Ollama `nomic-embed-text`
- **Vector Store**: ChromaDB (local, persisted)
- **Document parsing**: LangChain loaders (PyPDF, Docx2txt, TextLoader)

---

## Project Structure
```
rag_fullstack/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── rag_project/
│   │   ├── settings.py       # CORS, MEDIA_ROOT, CHROMA_DIR, DOCS_DIR
│   │   └── urls.py
│   ├── chatbot/
│   │   ├── models.py         # Document, ChatHistory
│   │   ├── views.py          # DocumentView, AskView, ChatHistoryView
│   │   ├── serializers.py    # DocumentSerializer, ChatHistorySerializer
│   │   ├── urls.py
│   │   ├── ingest.py         # Loads files, chunks, embeds, stores in Chroma
│   │   ├── rag_chain.py      # Retrieval + LLM chain with strict prompt
│   │   └── admin.py          # Admin for Document and ChatHistory
│   └── media/docs/           # Uploaded documents stored here
│
└── frontend/
    ├── package.json
    └── src/
        ├── App.jsx
        ├── api/api.js         # All Axios API calls
        ├── index.css
        └── components/
            ├── ChatBox.jsx    # Chat UI with message history
            ├── Message.jsx    # Single message bubble with sources
            ├── FileUpload.jsx # Drag & drop uploader
            └── DocumentList.jsx  # List + delete uploaded docs
```

---

## Core Concepts & Rules

### RAG Pipeline
1. Documents are uploaded → split into 500-char chunks (50 overlap) → embedded → stored in ChromaDB
2. User asks question → question is embedded → top 4 similar chunks retrieved → passed to LLM with strict prompt
3. LLM answers ONLY from retrieved context (temperature=0)

### Strict System Prompt (never change this pattern)
```
Answer ONLY using the context below.
If the answer is not in the context, say:
"I'm sorry, I don't have information about that in the provided documents."
Do NOT use outside knowledge. Do NOT make up answers.
```

### Key Settings
| Setting | Value | Why |
|---|---|---|
| `chunk_size` | 500 | Precise retrieval |
| `chunk_overlap` | 50 | Avoid missing context at boundaries |
| `k` (top chunks) | 4 | Balance context vs noise |
| `temperature` | 0 | Factual, deterministic answers |

---

## Django Models

### `Document`
```python
name: CharField
file: FileField(upload_to='docs/')
file_type: CharField   # .pdf / .docx / .txt
size: IntegerField     # bytes
uploaded_at: DateTimeField(auto_now_add=True)
indexed: BooleanField  # True after vectorstore build
```

### `ChatHistory`
```python
question: TextField
answer: TextField
sources: JSONField     # list of source file paths
asked_at: DateTimeField(auto_now_add=True)
```

---

## API Endpoints

| Method | URL | Purpose |
|---|---|---|
| GET | `/api/documents/` | List all uploaded documents |
| POST | `/api/documents/` | Upload a new document (multipart/form-data, field: `file`) |
| DELETE | `/api/documents/<id>/` | Delete document + re-index |
| POST | `/api/ask/` | Ask a question (`{"question": "..."}`) |
| GET | `/api/history/` | Get last 50 chat history items |
| DELETE | `/api/history/` | Clear all chat history |
| GET | `/api/health/` | Health check |

---

## Django Settings Required
```python
# In settings.py
CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
CHROMA_DIR = str(BASE_DIR / 'chroma_db')
DOCS_DIR = str(BASE_DIR / 'media' / 'docs')
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
```

---

## Ollama Models Used
- **LLM**: `ollama pull llama3.2` — used in `rag_chain.py`
- **Embeddings**: `ollama pull nomic-embed-text` — used in both `ingest.py` and `rag_chain.py`
- Ollama runs on `http://localhost:11434`

---

## Coding Conventions

### Backend (Django/Python)
- Views use class-based `APIView` from DRF
- Always validate file extension before saving: allowed = `['.pdf', '.docx', '.txt']`
- After any document upload or delete, call `build_vectorstore()` to re-index
- Save every Q&A to `ChatHistory` model
- Use `django.conf.settings` for all path configs (CHROMA_DIR, DOCS_DIR)
- Return consistent JSON: `{"message": "..."}` for success, `{"error": "..."}` for errors

### Frontend (React)
- All API calls go through `src/api/api.js` using the `API` axios instance
- Base URL is `http://localhost:8000/api`
- Components: `ChatBox`, `Message`, `FileUpload`, `DocumentList`
- Chat state lives in `ChatBox.jsx`
- Document refresh is triggered via a counter prop passed to `DocumentList`
- Use `Enter` to send message, `Shift+Enter` for newline

### LangChain
- Use `langchain_ollama` for `OllamaEmbeddings` and `OllamaLLM`
- Use `langchain_community.vectorstores.Chroma` for vector store
- Chain type is `"stuff"` (all chunks stuffed into prompt)
- Always pass `return_source_documents=True` to the chain

---

## Running the Project

```bash
# 1. Start Ollama
ollama serve

# 2. Django backend
cd backend
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# 3. React frontend
cd frontend
npm install
npm run dev
```

### Access
- React UI: `http://localhost:3000`
- Django Admin: `http://localhost:8000/admin`
- API root: `http://localhost:8000/api/`

---

## Common Tasks for Copilot

### Adding a new document type
1. Add extension to `ALLOWED_TYPES` in `views.py`
2. Add loader in `ingest.py` `load_documents()` function

### Switching LLM model
- Change `model="llama3.2"` in `rag_chain.py`
- Available local models: `llama3.1`, `llama3.2`, `mistral`, `gemma3`
- For OpenAI: replace `OllamaLLM` with `ChatOpenAI` from `langchain_openai`

### Switching to OpenAI
```python
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

### Switching to Groq (free cloud)
```python
from langchain_groq import ChatGroq
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
```

### Switching to Google Gemini (free tier)
```python
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
```

---

## Error Handling Patterns

### Backend — always return these shapes
```python
# Success
return Response({"message": "..."}, status=200)
return Response({...data...}, status=201)

# Client error
return Response({"error": "..."}, status=400)
return Response({"error": "Not found"}, status=404)

# Server error
return Response({"error": "Internal server error"}, status=500)
```

### Frontend — always handle errors in api.js calls
```javascript
try {
    const res = await someApiCall();
    // handle success
} catch (err) {
    const message = err.response?.data?.error || 'Something went wrong.';
    // show message to user
}
```

---

## Environment Variables

### Backend — use `.env` + `python-decouple` in production
```python
# .env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
OLLAMA_BASE_URL=http://localhost:11434
```

```python
# settings.py
from decouple import config
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
```

### Frontend — Vite env vars
```
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000/api
```

```javascript
// api/api.js
const API = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL });
```

---

## Django Admin Customization Patterns

```python
# Customize list display with computed fields
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'file_type', 'size_kb_display', 'indexed', 'uploaded_at']
    list_filter = ['indexed', 'file_type']
    search_fields = ['name']
    readonly_fields = ['uploaded_at', 'size']

    def size_kb_display(self, obj):
        return f"{round(obj.size / 1024, 1)} KB"
    size_kb_display.short_description = 'Size'
```

---

## Testing Patterns

### Backend — Django test cases
```python
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

class DocumentAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_upload_invalid_type(self):
        # should reject non-pdf/docx/txt files
        response = self.client.post('/api/documents/', {'file': mock_exe_file})
        self.assertEqual(response.status_code, 400)

    def test_ask_without_documents(self):
        response = self.client.post('/api/ask/', {'question': 'test'})
        self.assertEqual(response.status_code, 400)
```

### Frontend — component testing with Vitest
```javascript
import { render, screen } from '@testing-library/react';
import Message from '../components/Message';

test('renders bot message', () => {
    render(<Message msg={{ role: 'bot', content: 'Hello' }} />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
});
```

---

## Docker Setup (Production)

```yaml
# docker-compose.yml
version: "3.8"
services:
  ollama:
    image: ollama/ollama
    ports: ["11434:11434"]
    volumes:
      - ollama_data:/root/.ollama

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [ollama]
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    volumes:
      - ./backend/media:/app/media
      - ./backend/chroma_db:/app/chroma_db

  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on: [backend]

volumes:
  ollama_data:
```

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "rag_project.wsgi:application", "--bind", "0.0.0.0:8000"]
```

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json .
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

---

## Performance Tips

- **Re-indexing is slow** — avoid calling `build_vectorstore()` on every request; only call after upload/delete
- **ChromaDB cold start** — first query after server restart is slow (loading embeddings into memory)
- **Large files** — for PDFs > 10MB, consider async indexing with Django's `threading` module
- **k=4** — increase to `k=6` if answers feel incomplete; decrease to `k=2` for faster responses
- **Ollama GPU** — if server has NVIDIA GPU, Ollama auto-detects it — no config needed

---

## Security Notes
- Never expose `CHROMA_DIR` or `DOCS_DIR` via API
- Validate file types strictly — only allow `.pdf`, `.docx`, `.txt`
- Never allow path traversal in file names — sanitize using `os.path.basename(file.name)`
- CORS is restricted to `localhost:3000` in development — tighten in production
- Do not log or expose full file paths in API responses — use `file.name` only
- Set `DEBUG=False` in production — never deploy with `DEBUG=True`
- Use `SECRET_KEY` from environment variable, never hardcode it
- Limit upload file size — `DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800` (50MB max)
- Sanitize question input — strip and limit length before passing to LLM
```python
question = request.data.get('question', '')[:1000].strip()
```
