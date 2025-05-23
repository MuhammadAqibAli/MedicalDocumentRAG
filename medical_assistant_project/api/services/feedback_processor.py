import io
import uuid
import logging
from django.db import transaction
from api.models import Feedback, FeedbackAttachment
from api.utils.supabase_client import get_supabase_client
import os

logger = logging.getLogger(__name__)

def process_and_store_attachment(file_obj, feedback_instance):
    """
    Uploads a feedback attachment file to Supabase Storage and creates a FeedbackAttachment record.
    
    Args:
        file_obj: File object to process
        feedback_instance: Feedback instance to associate the attachment with
        
    Returns:
        FeedbackAttachment: The created attachment instance
    """
    supabase = get_supabase_client()
    file_content = file_obj.read()
    original_filename = file_obj.name
    file_extension = os.path.splitext(original_filename)[1].lower()
    
    # 1. Upload file to Supabase Storage
    storage_path = f"feedback-attachments/{uuid.uuid4()}_{original_filename}"  # Ensure unique path
    try:
        # Use correct content-type based on extension
        import mimetypes
        content_type = mimetypes.guess_type(original_filename)[0]
        if not content_type:
            content_type = 'application/octet-stream'
            
        upload_response = supabase.storage.from_("feedback-attachments").upload(  # Bucket name
            path=storage_path,
            file=file_content,
            file_options={"content-type": content_type}
        )
        logger.info(f"File uploaded to Supabase Storage: {storage_path}")
    except Exception as e:
        logger.error(f"Failed to upload file to Supabase Storage: {e}")
        raise ConnectionError("Failed to upload attachment to storage.") from e
    
    # 2. Create FeedbackAttachment record
    try:
        attachment = FeedbackAttachment.objects.create(
            feedback=feedback_instance,
            file_name=original_filename,
            supabase_storage_path=storage_path
        )
        logger.info(f"Created attachment record for feedback {feedback_instance.reference_number}")
        return attachment
    except Exception as e:
        # Clean up uploaded file if DB transaction fails
        try:
            supabase.storage.from_("feedback-attachments").remove([storage_path])
            logger.info(f"Cleaned up storage file {storage_path} after DB error.")
        except Exception as cleanup_e:
            logger.error(f"Failed to cleanup storage file {storage_path}: {cleanup_e}")
        raise

def get_feedback_attachment(attachment_id):
    """
    Retrieves a feedback attachment file from Supabase Storage.
    
    Args:
        attachment_id: UUID of the attachment to retrieve
        
    Returns:
        tuple: (file_content, file_name, content_type, error_message)
    """
    try:
        # Get attachment from database
        try:
            attachment = FeedbackAttachment.objects.get(id=attachment_id)
        except FeedbackAttachment.DoesNotExist:
            return None, None, None, f"Attachment with ID {attachment_id} not found."
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Get storage path from attachment
        storage_path = attachment.supabase_storage_path
        
        try:
            # Download file from Supabase storage
            file_content = supabase.storage.from_("feedback-attachments").download(storage_path)
            
            # Determine content type based on file extension
            import mimetypes
            content_type = mimetypes.guess_type(attachment.file_name)[0]
            if not content_type:
                content_type = 'application/octet-stream'
            
            return file_content, attachment.file_name, content_type, None
            
        except Exception as e:
            logger.error(f"Failed to download file from storage: {e}")
            return None, None, None, f"Failed to download attachment: {str(e)}"
            
    except Exception as e:
        logger.exception(f"Error downloading attachment {attachment_id}: {e}")
        return None, None, None, f"Error retrieving attachment: {str(e)}"

def delete_feedback_attachment(attachment_id):
    """
    Deletes a feedback attachment by ID, including its file in storage.
    
    Args:
        attachment_id: UUID of the attachment to delete
        
    Returns:
        tuple: (success, error_message)
    """
    try:
        # Get the attachment to check if it exists and to get storage path
        try:
            attachment = FeedbackAttachment.objects.get(id=attachment_id)
        except FeedbackAttachment.DoesNotExist:
            return False, f"Attachment with ID {attachment_id} not found."
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # 1. Delete file from Supabase storage
        storage_path = attachment.supabase_storage_path
        try:
            # Delete from the feedback-attachments bucket
            supabase.storage.from_("feedback-attachments").remove([storage_path])
            logger.info(f"Deleted file {storage_path} from Supabase storage")
        except Exception as e:
            logger.error(f"Failed to delete file from storage: {e}")
            # Continue with DB deletion even if storage deletion fails
        
        # 2. Delete attachment from database
        attachment.delete()
        logger.info(f"Deleted attachment {attachment_id} from database")
        
        return True, None  # Success, no error
        
    except Exception as e:
        logger.exception(f"Error deleting attachment {attachment_id}: {e}")
        return False, f"Failed to delete attachment: {str(e)}"
