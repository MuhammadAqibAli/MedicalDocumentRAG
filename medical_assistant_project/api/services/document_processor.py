import io
from pypdf import PdfReader
from docx import Document as DocxDocument
from langchain.text_splitter import RecursiveCharacterTextSplitter
from api.utils.embeddings import embed_texts
from api.utils.supabase_client import get_supabase_client
from api.models import Document, DocumentChunk
import logging
import os
from django.db import transaction
import uuid

logger = logging.getLogger(__name__)

# Configure chunking
CHUNK_SIZE = 1000 # Characters
CHUNK_OVERLAP = 150

def parse_pdf(file_content: bytes) -> str:
    """Extracts text from PDF content."""
    text = ""
    try:
        reader = PdfReader(io.BytesIO(file_content))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n" # Add newline between pages
    except Exception as e:
        logger.error(f"Error parsing PDF: {e}")
        raise ValueError("Could not parse PDF file.") from e
    return text

def parse_docx(file_content: bytes) -> str:
    """Extracts text from DOCX content."""
    text = ""
    try:
        doc = DocxDocument(io.BytesIO(file_content))
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        logger.error(f"Error parsing DOCX: {e}")
        raise ValueError("Could not parse DOCX file.") from e
    return text

def chunk_text(text: str) -> list[str]:
    """Chunks text using LangChain's splitter."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        add_start_index=True, # Helpful for potential metadata later
    )
    # Langchain splitter returns Document objects, extract page_content
    chunks = text_splitter.split_text(text)
    return chunks # Returns list of text strings

def process_and_store_document(file_obj, original_filename: str, standard_type_id: str):
    """
    Full pipeline: Reads file, uploads to Supabase Storage, parses, chunks,
    embeds, and saves everything to the database.
    
    Args:
        file_obj: File object to process
        original_filename: Original filename of the uploaded file
        standard_type_id: ID of the StandardType for this document
    """
    from api.models import StandardType  # Import here to avoid circular imports
    
    supabase = get_supabase_client()
    file_content = file_obj.read()
    file_extension = os.path.splitext(original_filename)[1].lower()

    # Validate standard_type_id
    try:
        standard_type = StandardType.objects.get(id=standard_type_id)
    except StandardType.DoesNotExist:
        raise ValueError(f"Standard type with ID {standard_type_id} not found.")

    # 1. Upload original file to Supabase Storage
    storage_path = f"documents/{uuid.uuid4()}_{original_filename}" # Ensure unique path
    try:
        # Use correct content-type based on extension
        content_type_map = {'.pdf': 'application/pdf', '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
        content_type = content_type_map.get(file_extension, 'application/octet-stream')

        upload_response = supabase.storage.from_("medical-documents").upload( # Bucket name
            path=storage_path,
            file=file_content,
            file_options={"content-type": content_type}
        )
        logger.info(f"File uploaded to Supabase Storage: {storage_path}")
    except Exception as e:
        logger.error(f"Failed to upload file to Supabase Storage: {e}")
        raise ConnectionError("Failed to upload to storage.") from e

    # 2. Parse text content
    if file_extension == ".pdf":
        text = parse_pdf(file_content)
    elif file_extension == ".docx":
        text = parse_docx(file_content)
    else:
        raise ValueError("Unsupported file type. Only PDF and DOCX are allowed.")

    if not text or text.isspace():
         raise ValueError("No text content extracted from the document.")

    # 3. Chunk the text
    text_chunks = chunk_text(text)
    if not text_chunks:
        logger.warning(f"No text chunks generated for document: {original_filename}")
        # Decide if you want to proceed without chunks or raise an error
        raise ValueError("Document processed but resulted in no text chunks.")


    # 4. Generate Embeddings (batch for efficiency)
    try:
        embeddings = embed_texts(text_chunks)
        logger.info(f"Generated {len(embeddings)} embeddings for {len(text_chunks)} chunks.")
    except Exception as e:
         logger.error(f"Failed to generate embeddings: {e}")
         # Consider cleaning up the uploaded file if embeddings fail
         # supabase.storage.from_("medical_documents").remove([storage_path])
         raise RuntimeError("Failed to generate embeddings.") from e

    # 5. Store in Database (using a transaction)
    try:
        with transaction.atomic():
            # Create Document record with standard_type as foreign key
            doc_instance = Document.objects.create(
                file_name=original_filename,
                standard_type=standard_type,  # Use the StandardType object
                supabase_storage_path=storage_path
                # Add any other metadata if needed
            )

            # Create DocumentChunk records in bulk
            chunks_to_create = []
            for i, chunk in enumerate(text_chunks):
                 if i < len(embeddings): # Safety check
                    chunk_data = DocumentChunk(
                        document=doc_instance,
                        chunk_text=chunk,
                        embedding=embeddings[i],
                        metadata={'chunk_index': i} # Example metadata
                    )
                    chunks_to_create.append(chunk_data)
                 else:
                     logger.warning(f"Mismatch between chunks and embeddings count for {original_filename}")
                     break # Avoid index error

            if chunks_to_create:
                 DocumentChunk.objects.bulk_create(chunks_to_create)
                 logger.info(f"Stored {len(chunks_to_create)} chunks in DB for document {doc_instance.id}")
            else:
                 logger.warning(f"No chunks were created in DB for document {doc_instance.id}")
                 # Potentially delete the doc_instance if no chunks were saved? Depends on requirements.

        return doc_instance # Return the created Document object

    except Exception as e:
        logger.error(f"Failed to save document and chunks to database: {e}")
        # Clean up uploaded file if DB transaction fails
        try:
            supabase.storage.from_("medical-documents").remove([storage_path])
            logger.info(f"Cleaned up storage file {storage_path} after DB error.")
        except Exception as cleanup_e:
            logger.error(f"Failed to cleanup storage file {storage_path}: {cleanup_e}")
        raise

def get_all_documents():
    """
    Retrieves all documents with metadata including derived extension type.
    Uses a join with StandardType table to get document type name.
    
    Returns:
        tuple: (documents_list, error_message)
            - documents_list: List of dictionaries containing document metadata or None if error
            - error_message: Error message or None if successful
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        import math
        
        # Use select_related to perform a join with StandardType table
        documents = Document.objects.select_related('standard_type').all().order_by('-uploaded_at')
        
        # Create a custom response with extension type and document type name
        result = []
        now = timezone.now()
        
        for doc in documents:
            # Extract extension from filename
            _, ext = os.path.splitext(doc.file_name)
            ext = ext.lower().lstrip('.')  # Remove dot and convert to lowercase
            
            # Calculate time difference
            time_diff = now - doc.uploaded_at
            days_diff = time_diff.days
            
            if days_diff == 0:
                hours = math.floor(time_diff.seconds / 3600)
                if hours == 0:
                    minutes = math.floor(time_diff.seconds / 60)
                    time_ago = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                else:
                    time_ago = f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif days_diff < 30:
                time_ago = f"{days_diff} day{'s' if days_diff != 1 else ''} ago"
            elif days_diff < 365:
                months = math.floor(days_diff / 30)
                time_ago = f"{months} month{'s' if months != 1 else ''} ago"
            else:
                years = math.floor(days_diff / 365)
                time_ago = f"{years} year{'s' if years != 1 else ''} ago"
            
            result.append({
                'id': doc.id,
                'file_name': doc.file_name,
                'standard_type_id': doc.standard_type.id,
                'standard_type_name': doc.standard_type.name,
                'uploaded_at': doc.uploaded_at,
                'time_ago': time_ago,
                'document_extension_type': ext
            })
        
        return result, None  # Return data and no error
        
    except Exception as e:
        logger.exception("Error retrieving documents: %s", str(e))
        return None, f"Failed to retrieve documents: {str(e)}"

def get_document_by_id(document_id):
    """
    Retrieves metadata for a single document by ID.
    Uses a join with StandardType table to get document type name.
    
    Args:
        document_id: UUID of the document to retrieve
        
    Returns:
        tuple: (document_data, error_message)
            - document_data: Dictionary with document metadata or None if error
            - error_message: Error message or None if successful
    """
    try:
        try:
            # Use select_related to perform a join with StandardType table
            document = Document.objects.select_related('standard_type').get(id=document_id)
        except Document.DoesNotExist:
            return None, f"Document with ID {document_id} not found."
        
        # Extract extension from filename
        _, ext = os.path.splitext(document.file_name)
        ext = ext.lower().lstrip('.')  # Remove dot and convert to lowercase
        
        # Create response with document metadata
        result = {
            'id': document.id,
            'file_name': document.file_name,
            'standard_type_id': document.standard_type.id,
            'standard_type_name': document.standard_type.name,
            'uploaded_at': document.uploaded_at,
            'document_extension_type': ext,
        }
        
        return result, None  # Return data and no error
        
    except Exception as e:
        logger.exception(f"Error retrieving document {document_id}: {e}")
        return None, f"Failed to retrieve document: {str(e)}"

def delete_document(document_id):
    """
    Deletes a document by ID, including its file in storage and related chunks.
    
    Args:
        document_id: UUID of the document to delete
        
    Returns:
        tuple: (success, error_message)
            - success: Boolean indicating if deletion was successful
            - error_message: Error message or None if successful
    """
    try:
        # Get the document to check if it exists and to get storage path
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return False, f"Document with ID {document_id} not found."
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # 1. Delete file from Supabase storage
        storage_path = document.supabase_storage_path
        try:
            # Delete from the medical-documents bucket
            supabase.storage.from_("medical-documents").remove([storage_path])
            logger.info(f"Deleted file {storage_path} from Supabase storage")
        except Exception as e:
            logger.error(f"Failed to delete file from storage: {e}")
            # Continue with DB deletion even if storage deletion fails
        
        # 2. Delete document and related chunks from database
        # Django will automatically delete related chunks due to CASCADE
        document.delete()
        logger.info(f"Deleted document {document_id} and its chunks from database")
        
        return True, None  # Success, no error
        
    except Exception as e:
        logger.exception(f"Error deleting document {document_id}: {e}")
        return False, f"Failed to delete document: {str(e)}"

def download_document(document_id):
    """
    Retrieves document file content and metadata for download.
    
    Args:
        document_id: UUID of the document to download
        
    Returns:
        tuple: (file_content, file_name, content_type, error_message)
            - file_content: Binary content of the file or None if error
            - file_name: Original filename or None if error
            - content_type: MIME type of the file or None if error
            - error_message: Error message or None if successful
    """
    try:
        # Get document from database
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return None, None, None, f"Document with ID {document_id} not found."
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Get storage path from document
        storage_path = document.supabase_storage_path
        
        try:
            # Download file from Supabase storage
            file_content = supabase.storage.from_("medical-documents").download(storage_path)
            
            # Determine content type based on file extension
            import mimetypes
            _, ext = os.path.splitext(document.file_name)
            content_type = mimetypes.guess_type(document.file_name)[0]
            if not content_type:
                # Default content types for common document formats
                content_type_map = {
                    '.pdf': 'application/pdf',
                    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                }
                content_type = content_type_map.get(ext.lower(), 'application/octet-stream')
            
            return file_content, document.file_name, content_type, None
            
        except Exception as e:
            logger.error(f"Failed to download file from storage: {e}")
            return None, None, None, f"Failed to download document: {str(e)}"
            
    except Exception as e:
        logger.exception(f"Error downloading document {document_id}: {e}")
        raise
