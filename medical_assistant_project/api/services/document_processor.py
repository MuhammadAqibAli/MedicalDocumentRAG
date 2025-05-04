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

def process_and_store_document(file_obj, original_filename: str, document_type: str):
    """
    Full pipeline: Reads file, uploads to Supabase Storage, parses, chunks,
    embeds, and saves everything to the database.
    """
    supabase = get_supabase_client()
    file_content = file_obj.read()
    file_extension = os.path.splitext(original_filename)[1].lower()

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
            # Create Document record
            doc_instance = Document.objects.create(
                file_name=original_filename,
                document_type=document_type,
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
            supabase.storage.from_("medical_documents").remove([storage_path])
            logger.info(f"Cleaned up storage file {storage_path} after DB error.")
        except Exception as cleanup_e:
            logger.error(f"Failed to cleanup storage file {storage_path}: {cleanup_e}")
        raise