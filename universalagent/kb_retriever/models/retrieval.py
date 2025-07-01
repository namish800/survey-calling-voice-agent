"""Data models for retrieval operations."""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class QueryRequest:
    """Request object for retrieval operations."""
    
    query: str
    similarity_top_k: int = 10
    similarity_threshold: Optional[float] = None
    metadata_filters: Optional[Dict[str, Any]] = None
    namespace: Optional[str] = None
    query_mode: str = "default"  # "default", "sparse", "hybrid"
    knowledge_base_ids: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate query request parameters."""
        if not self.query or not self.query.strip():
            raise ValueError("Query cannot be empty")
        
        if self.similarity_top_k <= 0:
            raise ValueError("similarity_top_k must be positive")
        
        if self.similarity_threshold is not None and not (0.0 <= self.similarity_threshold <= 1.0):
            raise ValueError("similarity_threshold must be between 0.0 and 1.0")
        
        if self.query_mode not in ["default", "sparse", "hybrid"]:
            raise ValueError("query_mode must be 'default', 'sparse', or 'hybrid'")


@dataclass
class RetrievedChunk:
    """A single retrieved node with content and metadata."""
    
    node_id: str
    content: str
    similarity_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_citation_info(self) -> Dict[str, Any]:
        """Get citation-friendly information from this node."""
        return {
            "node_id": self.node_id,
            "source_file": self.metadata.get("file_name", "Unknown"),
            "similarity_score": self.similarity_score,
            "content_preview": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "metadata": self.metadata,
        }
    
    def get_source_reference(self) -> str:
        """Get a human-readable source reference for citations."""
        source_file = self.metadata.get("file_name", "Unknown Source")
        page_num = self.metadata.get("page_number")
        
        if page_num:
            return f"{source_file} (Page {page_num})"
        return source_file
    
    def get_content_with_metadata(self) -> str:
        """Get content with relevant metadata context."""
        source_ref = self.get_source_reference()
        return f"[Source: {source_ref}]\n{self.content}"


@dataclass
class RetrievalResult:
    """Result of a retrieval operation."""
    
    success: bool
    chunks: List[RetrievedChunk] = field(default_factory=list)
    query_metadata: Dict[str, Any] = field(default_factory=dict)
    total_nodes_found: int = 0
    processing_time_seconds: float = 0.0
    error: Optional[Exception] = None
    
    def __post_init__(self):
        """Set total_nodes_found if not provided."""
        if self.total_nodes_found == 0:
            self.total_nodes_found = len(self.chunks)
    
    def get_top_nodes(self, count: int) -> List[RetrievedChunk]:
        """Get the top N nodes by similarity score."""
        return sorted(self.chunks, key=lambda x: x.similarity_score, reverse=True)[:count]
    
    def filter_by_similarity(self, threshold: float) -> List[RetrievedChunk]:
        """Filter nodes by minimum similarity threshold."""
        return [node for node in self.chunks if node.similarity_score >= threshold]
    
    def get_sources(self) -> List[str]:
        """Get unique source references from all nodes."""
        sources = set()
        for node in self.chunks:
            sources.add(node.get_source_reference())
        return sorted(list(sources))
    
    def get_citation_summary(self) -> Dict[str, Any]:
        """Get a summary suitable for citation purposes."""
        return {
            "total_nodes": len(self.chunks),
            "sources": self.get_sources(),
            "avg_similarity": sum(node.similarity_score for node in self.chunks) / len(self.chunks) if self.chunks else 0.0,
            "processing_time": self.processing_time_seconds,
            "query_metadata": self.query_metadata,
        }


@dataclass 
class EmbeddingConfig:
    """Configuration for embedding models."""
    
    api_key: str
    model_name: str = "text-embedding-3-small"
    batch_size: int = 100


@dataclass
class VectorStoreConfig:
    """Configuration for vector store connection."""
    
    api_key: str
    index_name: str
    namespace: Optional[str] = None
    environment: str = "us-east-1-aws"


@dataclass
class RetrievalConfig:
    """Configuration for retrieval operations."""
    
    embedding_config: EmbeddingConfig
    
    # Retrieval defaults
    default_similarity_top_k: int = 10
    default_similarity_threshold: Optional[float] = None
    default_query_mode: str = "default"
    
    # Performance settings
    request_timeout_seconds: float = 30.0
    max_retries: int = 3
    
    # Postprocessing options
    enable_similarity_filter: bool = True
    enable_keyword_filter: bool = False
    similarity_cutoff: float = 0.7
    
    def __post_init__(self):
        """Validate configuration."""
        if self.default_similarity_top_k <= 0:
            raise ValueError("default_similarity_top_k must be positive")
        
        if self.default_similarity_threshold is not None and not (0.0 <= self.default_similarity_threshold <= 1.0):
            raise ValueError("default_similarity_threshold must be between 0.0 and 1.0")
        
        if self.request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be positive")
        
        if not (0.0 <= self.similarity_cutoff <= 1.0):
            raise ValueError("similarity_cutoff must be between 0.0 and 1.0") 