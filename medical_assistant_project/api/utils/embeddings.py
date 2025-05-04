from langchain_huggingface import HuggingFaceEmbeddings
import os

# Configure the embedding model (ensure dimensions match models.py VectorField)
# Make sure the model is downloaded or accessible
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2" # 384 dimensions

def get_embedding_model():
    """Initializes and returns the HuggingFace embedding model."""
    # Specify cache directory if needed, especially in server environments
    # cache_folder = os.path.join(os.getcwd(), ".embedding_cache")
    # os.makedirs(cache_folder, exist_ok=True)

    # device = 'cuda' if torch.cuda.is_available() else 'cpu' # If you want GPU acceleration
    model_kwargs = {'device': 'cpu'} # Use 'cuda' for GPU
    encode_kwargs = {'normalize_embeddings': False} # Normalization preference

    embeddings = HuggingFaceEmbeddings(
        model_name=MODEL_NAME,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
        # cache_folder=cache_folder
    )
    return embeddings

# Singleton pattern to avoid reloading the model repeatedly
embedding_model_instance = None

def get_cached_embedding_model():
    global embedding_model_instance
    if embedding_model_instance is None:
        embedding_model_instance = get_embedding_model()
    return embedding_model_instance

def embed_text(text: str) -> list[float]:
    """Generates embedding for a single text string."""
    model = get_cached_embedding_model()
    return model.embed_query(text)

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generates embeddings for a list of text strings."""
    model = get_cached_embedding_model()
    return model.embed_documents(texts)