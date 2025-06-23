"""Interface for retrieval pipelines."""

from abc import ABC, abstractmethod
from typing import Protocol

from kb_retriever.models.retrieval import QueryRequest, RetrievalResult


class IRetrievalPipeline(ABC):
    """Interface for retrieval pipeline implementations.
    
    This interface focuses on pure retrieval operations but is designed
    to be extensible for future query engine capabilities.
    """
    
    @abstractmethod
    async def retrieve(self, request: QueryRequest) -> RetrievalResult:
        """Retrieve relevant nodes for the given query.
        
        Args:
            request: The query request with search parameters
            
        Returns:
            RetrievalResult containing retrieved nodes and metadata
        """
        pass
    
    @abstractmethod
    async def validate_query(self, request: QueryRequest) -> bool:
        """Validate if the query request can be processed.
        
        Args:
            request: The query request to validate
            
        Returns:
            True if the query is valid and can be processed, False otherwise
        """
        pass


# Future extensibility: IQueryEngine interface for when we add response synthesis
class IQueryEngine(Protocol):
    """Future interface for query engines with response synthesis.
    
    This is a protocol definition for future implementation that would
    extend IRetrievalPipeline with LLM-powered response generation.
    """
    
    async def retrieve(self, request: QueryRequest) -> RetrievalResult:
        """Retrieve relevant nodes for the given query."""
        ...
    
    async def query(self, request: QueryRequest) -> "QueryEngineResult":
        """Generate an answer using retrieved context and LLM synthesis."""
        ... 