from celery import shared_task


@shared_task
def process_document_task(document_id):
    from .models import Document
    from rag.pipeline import process_document

    try:
        document = Document.objects.get(id=document_id)
        document.status = Document.Status.PROCESSING
        document.save(update_fields=["status"])

        chunk_count = process_document(document)

        document.status = Document.Status.READY
        document.error_message = None
        document.save(update_fields=["status", "error_message"])

        print(f"[Celery] Document {document_id} processed into {chunk_count} chunks")

    except Document.DoesNotExist:
        print(f"[Celery] Document {document_id} not found")

    except Exception as e:
        try:
            document.status = Document.Status.FAILED
            document.error_message = str(e)
            document.save(update_fields=["status", "error_message"])
        except Exception:
            pass
        print(f"[Celery] Failed processing document {document_id}: {e}")