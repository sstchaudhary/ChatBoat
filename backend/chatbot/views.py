import json
import os
import shutil
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import StreamingHttpResponse
from .models import Document, ChatHistory
from .serializers import DocumentSerializer, ChatHistorySerializer
from .ingest import build_vectorstore, index_document, ALLOWED_TYPES, load_documents
from .rag_chain import ask, ask_stream


class DocumentView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        docs = Document.objects.all().order_by('-uploaded_at')
        serializer = DocumentSerializer(docs, many=True)
        return Response(serializer.data)

    def post(self, request):
        f = request.FILES.get('file')
        if not f:
            return Response({'error': 'file required'}, status=status.HTTP_400_BAD_REQUEST)
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in ALLOWED_TYPES:
            return Response({'error': 'invalid file type'}, status=status.HTTP_400_BAD_REQUEST)
        os.makedirs(settings.DOCS_DIR, exist_ok=True)
        path = default_storage.save(os.path.join('docs', f.name), f)
        doc = Document.objects.create(name=f.name, file=path, file_type=ext, size=f.size, indexed=False)
        
        try:
            index_document(doc.file.path)
        except Exception as exc:
            return Response(
                {
                    'message': 'uploaded, but indexing failed',
                    'document_id': doc.id,
                    'indexed': False,
                    'warning': str(exc),
                },
                status=status.HTTP_201_CREATED,
            )

        doc.indexed = True
        doc.save(update_fields=['indexed'])
        return Response(
            {'message': 'uploaded', 'document_id': doc.id, 'indexed': True},
            status=status.HTTP_201_CREATED,
        )


class DocumentDeleteView(APIView):
    def delete(self, request, doc_id):
        try:
            doc = Document.objects.get(pk=doc_id)
        except Document.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Explicitly delete the file from disk
        file_path = os.path.join(settings.DOCS_DIR, doc.name)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✓ Deleted file: {file_path}")
            except Exception as e:
                print(f"✗ Error deleting file {file_path}: {str(e)}")
        
        # Also try Django's delete method
        doc.file.delete(save=False)
        
        # Delete database record
        doc.delete()
        print(f"✓ Deleted document record: {doc_id}")
        
        # IMMEDIATELY clear the vectorstore (synchronous - don't return until done)
        if os.path.exists(settings.CHROMA_DIR):
            try:
                shutil.rmtree(settings.CHROMA_DIR)
                print(f"✓ Deleted vectorstore: {settings.CHROMA_DIR}")
            except Exception as e:
                print(f"✗ Error deleting vectorstore: {str(e)}")
        
        # Rebuild vectorstore synchronously BEFORE responding
        # This ensures no old data is accessible after deletion
        try:
            build_vectorstore()
            print("✓ Rebuilt vectorstore with remaining documents")
        except Exception as e:
            print(f"✗ Error rebuilding vectorstore: {str(e)}")
        
        return Response({'message': 'Document and all associated data deleted completely'})


class AskView(APIView):
    def post(self, request):
        question = request.data.get('question', '').strip()
        conversation = request.data.get('conversation', [])
        if not question:
            return Response({'error': 'question required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            res = ask(question, conversation)
        except RuntimeError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {'error': 'ask failed', 'details': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        ChatHistory.objects.create(question=question, answer=res.get('answer', ''), sources=res.get('sources', []))
        return Response(res)


class AskStreamView(APIView):
    def post(self, request):
        question = request.data.get('question', '').strip()
        conversation = request.data.get('conversation', [])
        if not question:
            return Response({'error': 'question required'}, status=status.HTTP_400_BAD_REQUEST)

        def event_stream():
            answer_parts = []
            sources = []
            completed = False
            try:
                for chunk in ask_stream(question, conversation):
                    if chunk['type'] == 'token':
                        answer_parts.append(chunk['text'])
                        yield f"data: {json.dumps({'type': 'token', 'text': chunk['text']})}\n\n"
                    elif chunk['type'] == 'done':
                        sources = chunk.get('sources', [])
                        completed = True
                        yield f"data: {json.dumps(chunk)}\n\n"
                    elif chunk['type'] == 'error':
                        yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as exc:
                yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
            finally:
                if completed and answer_parts:
                    full_answer = ''.join(answer_parts)
                    try:
                        ChatHistory.objects.create(
                            question=question,
                            answer=full_answer,
                            sources=sources,
                        )
                    except Exception:
                        pass

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response


class ChatHistoryView(APIView):
    def get(self, request):
        items = ChatHistory.objects.all().order_by('-asked_at')[:50]
        serializer = ChatHistorySerializer(items, many=True)
        return Response(serializer.data)


class HealthView(APIView):
    def get(self, request):
        return Response({
            'status': 'ok',
            'documents': Document.objects.count(),
            'chats': ChatHistory.objects.count()
        })


class DebugDocumentsView(APIView):
    """Debug endpoint: show what text is extracted from each document."""
    def get(self, request):
        docs_data = []
        docs = load_documents()
        for doc in docs:
            text_preview = doc['text'][:500] if doc['text'] else '(empty)'
            text_length = len(doc['text'])
            docs_data.append({
                'source': doc['source'],
                'text_length': text_length,
                'text_preview': text_preview,
                'status': 'indexed' if text_length > 20 else 'skipped',
            })
        
        # Also show all files in docs folder
        all_files = []
        if os.path.exists(settings.DOCS_DIR):
            for name in os.listdir(settings.DOCS_DIR):
                path = os.path.join(settings.DOCS_DIR, name)
                if os.path.isfile(path):
                    ext = os.path.splitext(name)[1].lower()
                    size = os.path.getsize(path)
                    
                    # Try to extract preview
                    preview = '(error)'
                    status = 'unknown'
                    try:
                        if ext == '.pdf':
                            from .ingest import extract_pdf_text
                            text, status_msg = extract_pdf_text(path)
                            preview = text[:200] if text else status_msg
                            status = status_msg
                        elif ext == '.txt':
                            with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
                                text = fh.read()
                            preview = text[:200]
                            status = 'readable' if len(text) > 20 else 'too short'
                        elif ext == '.docx':
                            import docx2txt
                            text = docx2txt.process(path) or ''
                            preview = text[:200] if text else '(empty)'
                            status = 'readable' if text else 'empty'
                    except Exception as e:
                        status = f'error: {str(e)}'
                    
                    all_files.append({
                        'name': name,
                        'size_kb': round(size / 1024, 2),
                        'type': ext,
                        'status': status,
                        'preview': preview,
                    })
        
        return Response({
            'indexed_documents': docs_data,
            'all_files': all_files,
            'total_indexed': len(docs),
            'total_files': len(all_files),
        })


class ClearVectorstoreView(APIView):
    """Clear ChromaDB completely and rebuild from scratch."""
    def post(self, request):
        try:
            if os.path.exists(settings.CHROMA_DIR):
                shutil.rmtree(settings.CHROMA_DIR)
            
            build_vectorstore()
            return Response({'message': 'Vectorstore cleared and rebuilt.'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)
