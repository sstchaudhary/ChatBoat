import os
import re

from django.conf import settings
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_core.prompts import PromptTemplate

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

# Greeting patterns - detect casual greetings
GREETING_PATTERNS = [
    r'\b(hello|hi|hey|greetings|howdy|what\'s\s*up|how\s+are\s+you|good\s+(morning|afternoon|evening)|nice\s+to\s+meet|thanks?|thank\s+you)\b',
]

GREETING_RESPONSES = {
    'en': "Hello! 👋 I'm here to help. Upload a document and ask me anything about it!",
    'es': "¡Hola! 👋 Estoy aquí para ayudarte. ¡Sube un documento y pregúntame cualquier cosa sobre él!",
    'fr': "Bonjour! 👋 Je suis là pour vous aider. Téléchargez un document et posez-moi n'importe quelle question à son sujet!",
    'de': "Hallo! 👋 Ich bin hier, um zu helfen. Laden Sie ein Dokument hoch und stellen Sie mir eine beliebige Frage dazu!",
    'hi': "नमस्ते! 👋 मैं आपकी मदद के लिए यहाँ हूँ। एक दस्तावेज़ अपलोड करें और मुझसे इसके बारे में कोई भी प्रश्न पूछें!",
}

SYSTEM_PROMPT = PromptTemplate(
    input_variables=["context", "conversation", "question"],
    template=(
        "You are a helpful document assistant. Answer ONLY using the context provided below.\n"
        "IMPORTANT RULES:\n"
        "1. Generate your answer in the SAME language as the context/documents.\n"
        "2. Be COMPREHENSIVE and DETAILED — cover ALL relevant points found in the context.\n"
        "3. FORMAT YOUR RESPONSE USING MARKDOWN:\n"
        "   - Use headings (### or ####) to organize information into logical sections\n"
        "   - Use bullet points (-) for lists of items or features\n"
        "   - Use bold (**text**) to emphasize important terms or conditions\n"
        "   - Use numbered lists (1. 2. 3.) when describing steps or sequences\n"
        "4. Include ALL details, conditions, eligibility criteria, exceptions, and specifics mentioned.\n"
        "5. Do NOT summarize or shorten — give the COMPLETE information from the context.\n"
        "6. If the answer is not in the context, say: 'I\\'m sorry, I don\\'t have information about that in the provided documents.'\n"
        "7. Do NOT use outside knowledge — only use what is in the context below.\n\n"
        "Context:\n{context}\n\nConversation so far:\n{conversation}\n\nQuestion: {question}\n\nFormatted Answer:"
    ),
)


def is_greeting(question: str) -> bool:
    """Detect if question is a greeting or casual message."""
    question_lower = question.lower().strip()
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, question_lower):
            return True
    return False


def load_vectorstore():
    embeddings = OllamaEmbeddings(model='nomic-embed-text')
    chroma_dir = settings.CHROMA_DIR
    if not os.path.exists(chroma_dir):
        raise RuntimeError('No documents found. Upload a document and wait for indexing to complete.')
    return Chroma(persist_directory=chroma_dir, embedding_function=embeddings)


def format_conversation(conversation) -> str:
    if not isinstance(conversation, list):
        return '(No previous conversation.)'

    entries = []
    for message in conversation[-10:]:
        if not isinstance(message, dict):
            continue
        role = message.get('role')
        content = str(message.get('content', '')).strip()
        if role not in ('user', 'bot') or not content:
            continue
        speaker = 'User' if role == 'user' else 'Assistant'
        entries.append(f'{speaker}: {content[:2000]}')

    return '\n\n'.join(entries) if entries else '(No previous conversation.)'


def ask_stream(question: str, conversation=None):
    """
    Generator that yields tokens as the LLM produces them.
    Each yielded item is a dict:
      {'type': 'token',  'text': '...'}
      {'type': 'done',   'sources': [...], 'is_greeting': bool}
      {'type': 'error',  'message': '...'}
    """
    if is_greeting(question):
        greeting = GREETING_RESPONSES.get('en', "Hello! I'm here to help. Upload a document and ask me anything!")
        yield {'type': 'token', 'text': greeting}
        yield {'type': 'done', 'sources': [], 'is_greeting': True}
        return

    try:
        vectorstore = load_vectorstore()
    except RuntimeError as exc:
        yield {'type': 'error', 'message': str(exc)}
        return

    try:
        docs = vectorstore.similarity_search(question, k=5)
    finally:
        try:
            vectorstore._client.close()
        except Exception:
            pass

    if not docs:
        yield {'type': 'error', 'message': 'No documents found. Upload a document and wait for indexing to complete.'}
        return

    context = "\n\n".join(
        f"Source: {doc.metadata.get('source', 'unknown')}\n{doc.page_content}"
        for doc in docs
    )

    if not context.strip() or len(context.strip()) < 50:
        yield {'type': 'token', 'text': "I'm sorry, I don't have information about that in the provided documents."}
        yield {'type': 'done', 'sources': [], 'is_greeting': False}
        return

    prompt = SYSTEM_PROMPT.format(
        context=context,
        conversation=format_conversation(conversation),
        question=question,
    )
    llm_model = os.environ.get('OLLAMA_LLM_MODEL', 'llama3.2')
    llm = OllamaLLM(model=llm_model, temperature=0.2)

    sources = list(dict.fromkeys(doc.metadata.get('source', 'unknown') for doc in docs))

    for chunk in llm.stream(prompt):
        if chunk:
            yield {'type': 'token', 'text': chunk}

    yield {'type': 'done', 'sources': sources, 'is_greeting': False}


def ask(question: str, conversation=None) -> dict:
    """
    Answer questions about indexed documents.
    - Detects greetings and responds with a friendly greeting.
    - For real questions, retrieves relevant document chunks and generates answers in the document's language.
    """
    
    # Handle greetings
    if is_greeting(question):
        return {
            'answer': GREETING_RESPONSES.get('en', "Hello! I'm here to help. Upload a document and ask me anything about it!"),
            'sources': [],
            'is_greeting': True,
        }
    
    vectorstore = load_vectorstore()
    try:
        docs = vectorstore.similarity_search(question, k=10)
    finally:
        # Always release the Chroma connection to avoid Windows file locks
        try:
            vectorstore._client.close()
        except Exception:
            pass
    if not docs:
        raise RuntimeError('No documents found. Upload a document and wait for indexing to complete.')

    context = "\n\n".join(
        f"Source: {doc.metadata.get('source', 'unknown')}\n{doc.page_content}"
        for doc in docs
    )
    
    # Check if context is empty or too minimal
    if not context.strip() or len(context.strip()) < 50:
        return {
            'answer': "I'm sorry, I don't have information about that in the provided documents. The document may be image-based or have no extractable text.",
            'sources': [],
            'is_greeting': False,
        }
    
    prompt = SYSTEM_PROMPT.format(
        context=context,
        conversation=format_conversation(conversation),
        question=question,
    )
    llm_model = os.environ.get('OLLAMA_LLM_MODEL', 'llama3.2')
    llm = OllamaLLM(model=llm_model, temperature=0.2)
    answer = llm.invoke(prompt)
    if not isinstance(answer, str):
        answer = str(answer)
    
    sources = [getattr(doc, 'metadata', {}).get('source', 'unknown') for doc in docs]
    
    return {'answer': answer, 'sources': list(dict.fromkeys(sources)), 'is_greeting': False}
