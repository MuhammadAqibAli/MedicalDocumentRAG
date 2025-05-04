import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Initializes and returns the Supabase client using service role."""
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_SERVICE_KEY") # Use service key for backend operations
    if not url or not key:
        raise ValueError("Supabase URL or Service Key not found in environment variables.")
    return create_client(url, key)

def get_supabase_anon_client() -> Client:
    """Initializes and returns the Supabase client using anon key (for public access if needed)."""
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        raise ValueError("Supabase URL or Anon Key not found in environment variables.")
    return create_client(url, key)

# You can add helper functions here for upload/download if desired
# e.g., upload_to_storage, download_from_storage