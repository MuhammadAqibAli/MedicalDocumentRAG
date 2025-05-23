import logging
import uuid
from django.db import transaction
from ..models import Complaint
from ..utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

def upload_complaint_file(file_obj, original_filename: str):
    """
    Uploads a complaint file to Supabase storage and returns the storage path.
    
    Args:
        file_obj: File object to upload
        original_filename: Original filename of the uploaded file
    
    Returns:
        str: The storage path in Supabase
    """
    supabase = get_supabase_client()
    file_content = file_obj.read()
    
    # Create a unique storage path
    storage_path = f"complaints/{uuid.uuid4()}_{original_filename}"
    
    try:
        # Upload file to Supabase storage
        upload_response = supabase.storage.from_("medical-documents").upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": "application/octet-stream"}
        )
        logger.info(f"Complaint file uploaded to Supabase Storage: {storage_path}")
        return storage_path, None
    except Exception as e:
        logger.error(f"Failed to upload complaint file to Supabase Storage: {e}")
        return None, str(e)

def get_all_complaints():
    """
    Retrieves all complaints.
    
    Returns:
        list: List of complaint objects
    """
    try:
        complaints = Complaint.objects.all().order_by('-created_at')
        return complaints, None
    except Exception as e:
        logger.error(f"Error retrieving complaints: {e}")
        return None, str(e)

def get_complaint_by_id(complaint_id):
    """
    Retrieves a specific complaint by ID.
    
    Args:
        complaint_id: UUID of the complaint to retrieve
    
    Returns:
        Complaint: The complaint object if found
    """
    try:
        complaint = Complaint.objects.get(id=complaint_id)
        return complaint, None
    except Complaint.DoesNotExist:
        return None, f"Complaint with ID {complaint_id} not found."
    except Exception as e:
        logger.error(f"Error retrieving complaint {complaint_id}: {e}")
        return None, str(e)

def delete_complaint(complaint_id):
    """
    Deletes a complaint and its associated file in storage.
    
    Args:
        complaint_id: UUID of the complaint to delete
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        complaint = Complaint.objects.get(id=complaint_id)
        
        # Delete file from storage if it exists
        if complaint.file_upload_path:
            try:
                supabase = get_supabase_client()
                supabase.storage.from_("medical-documents").remove([complaint.file_upload_path])
                logger.info(f"Deleted file from storage: {complaint.file_upload_path}")
            except Exception as e:
                logger.error(f"Error deleting file from storage: {e}")
                # Continue with complaint deletion even if file deletion fails
        
        # Delete the complaint
        complaint.delete()
        return True, None
    except Complaint.DoesNotExist:
        return False, f"Complaint with ID {complaint_id} not found."
    except Exception as e:
        logger.error(f"Error deleting complaint {complaint_id}: {e}")
        return False, str(e)
