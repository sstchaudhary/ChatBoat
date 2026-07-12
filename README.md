# RAG Fullstack Project

Document-based RAG chatbot built with Django, React, and Ollama.

## Requirements

- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.com/)

Pull the required Ollama models before starting the backend:

```powershell
ollama pull llama3.2
ollama pull nomic-embed-text
```

## Run the Backend

```powershell
cd D:\AIProject\backend
.\create_venv.ps1
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The backend runs at `http://localhost:8000`.

## Run the Frontend

```powershell
cd D:\AIProject\frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

## Document Upload Flow

Upload a PDF, DOCX, or TXT document from the frontend. The backend saves the
file and adds that document to the existing vector store during the same
request, then returns the final indexing status. No Celery worker, Redis, or
RabbitMQ service is needed.

If the vector store cannot be rebuilt, the file remains uploaded and the API
returns `indexed: false` with a warning.

## Useful API Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET/POST /api/documents/` | List or upload documents |
| `DELETE /api/documents/<id>/` | Delete a document and rebuild the index |
| `POST /api/ask/` | Ask a question |
| `POST /api/ask/stream/` | Ask a question with streamed output |
| `GET /api/health/` | Check backend health |

## Troubleshooting

- Start Ollama with `ollama serve` if the backend cannot create embeddings.
- Ensure the `nomic-embed-text` model is installed for document indexing.
- Scanned PDFs require OCR; PDFs with extractable text work directly.
