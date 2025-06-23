"""KB Retriever package for semantic document retrieval."""

from .interfaces.retrieval import IRetrievalPipeline
from .llamaindex_document_retrieval import LlamaIndexDocumentRetrievalFromPinecone
from .models.retrieval import (
    EmbeddingConfig,
    QueryRequest,
    RetrievalConfig,
    RetrievalResult,
    RetrievedChunk,
    VectorStoreConfig,
)

__version__ = "0.1.0"

__all__ = [
    # Core interface
    "IRetrievalPipeline",
    
    # Concrete implementation
    "LlamaIndexDocumentRetrievalFromPinecone",
    
    # Data models
    "QueryRequest",
    "RetrievedChunk", 
    "RetrievalResult",
    
    # Configuration models
    "RetrievalConfig",
    "EmbeddingConfig",
    "VectorStoreConfig",
]

