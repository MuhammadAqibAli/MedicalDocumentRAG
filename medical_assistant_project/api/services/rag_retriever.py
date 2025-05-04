from api.models import DocumentChunk
from api.utils.embeddings import embed_text
from pgvector.django import CosineDistance # Or L2Distance, InnerProduct
import logging

logger = logging.getLogger(__name__)

DEFAULT_SIMILARITY_THRESHOLD = 0.75 # Adjust based on experimentation (Cosine similarity: higher is better)
DEFAULT_TOP_K = 5 # Number of chunks to retrieve

def retrieve_relevant_chunks(query: str, top_k: int = DEFAULT_TOP_K, similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD):
    """
    Embeds the query and searches for similar document chunks in the database.
    """
    try:
        query_embedding = embed_text(query)
    except Exception as e:
        logger.error(f"Failed to embed query '{query[:50]}...': {e}")
        return None, "Failed to embed query"

    try:
        # Use pgvector's CosineDistance (1 - cosine_similarity)
        # Lower distance means higher similarity
        # Order by distance ascending and filter
        results = DocumentChunk.objects.annotate(
            distance=CosineDistance('embedding', query_embedding)
        ).filter(
            distance__lte=(1 - similarity_threshold) # Convert similarity threshold to max distance
        ).order_by('distance')[:top_k]

        if not results:
            logger.info(f"No relevant chunks found for query '{query[:50]}...' with threshold {similarity_threshold}")
            return None, "No relevant documents found."

        # Format results for context
        context = "\n---\n".join([chunk.chunk_text for chunk in results])
        source_chunk_ids = [str(chunk.id) for chunk in results] # Get IDs for traceability

        logger.info(f"Retrieved {len(results)} relevant chunks for query '{query[:50]}...'")
        return context, source_chunk_ids

    except Exception as e:
        logger.error(f"Error during vector search for query '{query[:50]}...': {e}")
        return None, f"Database search error: {e}"