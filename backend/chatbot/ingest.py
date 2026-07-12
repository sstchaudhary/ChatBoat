import os
import docx2txt
from pypdf import PdfReader
from django.conf import settings

ALLOWED_TYPES = ['.pdf', '.docx', '.txt']


def chunk_text(text, chunk_size=1000, overlap=150):
    chunks = []
    start = 0
    text = text or ''
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def extract_pdf_text(path):
    """Extract text from PDF using multiple methods."""
    text = ''
    try:
        reader = PdfReader(path)
        if not reader.pages:
            return '', 'No pages found'
        
        # Try standard text extraction first
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text() or ''
                text += page_text + '\n'
            except Exception as e:
                print(f"Error extracting page {page_num}: {str(e)}")
        
        text = text.strip()
        
        # Check extraction quality
        if not text:
            return '', 'No text extracted (possibly scanned/image PDF - need OCR)'
        
        if len(text) < 50:
            return '', f'Very little text extracted ({len(text)} chars) - may be scanned'
        
        return text, 'success'
    except Exception as e:
        return '', f'PDF extraction error: {str(e)}'


def extract_document_text(path):
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == '.txt':
            with open(path, 'r', encoding='utf-8', errors='ignore') as file_handle:
                return file_handle.read(), 'success'
        if ext == '.pdf':
            return extract_pdf_text(path)
        if ext == '.docx':
            text = docx2txt.process(path) or ''
            return text, 'success' if text else 'No text extracted from DOCX'
    except Exception as exc:
        return '', f'Error: {str(exc)}'

    return '', 'Unsupported file type'


def load_documents():
    docs = []
    docs_dir = settings.DOCS_DIR
    if not os.path.exists(docs_dir):
        return docs

    for name in os.listdir(docs_dir):
        path = os.path.join(docs_dir, name)
        if not os.path.isfile(path):
            continue

        ext = os.path.splitext(name)[1].lower()
        if ext not in ALLOWED_TYPES:
            continue

        text, status = extract_document_text(path)

        if text and len(text.strip()) > 20:
            docs.append({'source': name, 'text': text})
            print(f"✓ Loaded: {name} ({len(text)} chars)")
        else:
            print(f"✗ Skipped {name}: {status}")

    return docs


def index_document(path):
    try:
        from langchain_ollama import OllamaEmbeddings
        try:
            from langchain_chroma import Chroma
        except ImportError:
            from langchain_community.vectorstores import Chroma
    except Exception as exc:
        raise RuntimeError('Missing RAG dependencies: ' + str(exc)) from exc

    text, status = extract_document_text(path)
    if not text or len(text.strip()) <= 20:
        raise ValueError(f'Could not extract usable text: {status}')

    texts = chunk_text(text, chunk_size=1000, overlap=150)
    metadatas = [{'source': os.path.basename(path)} for _ in texts]
    embeddings = OllamaEmbeddings(model='nomic-embed-text')
    vectorstore = None

    try:
        if os.path.exists(settings.CHROMA_DIR):
            vectorstore = Chroma(
                persist_directory=settings.CHROMA_DIR,
                embedding_function=embeddings,
            )
            vectorstore.add_texts(texts=texts, metadatas=metadatas)
        else:
            vectorstore = Chroma.from_texts(
                texts=texts,
                metadatas=metadatas,
                embedding=embeddings,
                persist_directory=settings.CHROMA_DIR,
            )
    finally:
        if vectorstore is not None:
            try:
                vectorstore._client.close()
            except Exception:
                pass


def build_vectorstore():
    try:
        from langchain_ollama import OllamaEmbeddings
        try:
            from langchain_chroma import Chroma
        except ImportError:
            from langchain_community.vectorstores import Chroma
    except Exception as e:
        raise RuntimeError('Missing RAG dependencies: ' + str(e))

    import shutil
    import time

    os.makedirs(settings.DOCS_DIR, exist_ok=True)

    # Clear old Chroma DB — retry on Windows file lock errors
    if os.path.exists(settings.CHROMA_DIR):
        for attempt in range(5):
            try:
                shutil.rmtree(settings.CHROMA_DIR)
                break
            except PermissionError:
                if attempt < 4:
                    time.sleep(1)  # wait for file lock to release
                else:
                    raise

    os.makedirs(settings.CHROMA_DIR, exist_ok=True)

    docs = load_documents()
    texts = []
    metadatas = []
    for d in docs:
        for chunk in chunk_text(d['text'], chunk_size=1000, overlap=150):
            texts.append(chunk)
            metadatas.append({'source': d['source']})

    if not texts:
        return

    embeddings = OllamaEmbeddings(model='nomic-embed-text')
    vectorstore = Chroma.from_texts(
        texts=texts,
        metadatas=metadatas,
        embedding=embeddings,
        persist_directory=settings.CHROMA_DIR,
    )
    try:
        vectorstore._client.close()
    except Exception:
        pass
