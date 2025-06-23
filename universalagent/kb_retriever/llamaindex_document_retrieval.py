"""LlamaIndex-based document retrieval from Pinecone vector store."""

import time
from typing import List, Optional

from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores import VectorStoreQuery
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.pinecone import PineconeVectorStore
from pinecone import Pinecone

from kb_retriever.interfaces.retrieval import IRetrievalPipeline
from kb_retriever.models.retrieval import (
    QueryRequest,
    RetrievalResult,
    RetrievedChunk,
    RetrievalConfig,
)


class LlamaIndexDocumentRetrievalFromPinecone(IRetrievalPipeline):
    """LlamaIndex-based document retrieval using Pinecone vector store.
    
    This implementation provides semantic search capabilities over documents
    stored in Pinecone, using OpenAI embeddings for query encoding.
    """
    
    def __init__(self, config: RetrievalConfig, vector_store: PineconeVectorStore):
        """Initialize the retrieval pipeline.
        
        Args:
            config: Configuration for retrieval operations
        """
        self.config = config
        
        # Initialize embedding model
        self.embedding_model = OpenAIEmbedding(
            api_key=config.embedding_config.api_key,
            model=config.embedding_config.model_name,
        )

        # Initialize vector store
        self.vector_store = vector_store
        
        # Create vector index for retrieval
        self.vector_index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            embed_model=self.embedding_model,
        )
    
    async def retrieve(self, request: QueryRequest) -> RetrievalResult:
        """Retrieve relevant nodes for the given query.
        
        Args:
            request: The query request with search parameters
            
        Returns:
            RetrievalResult containing retrieved nodes and metadata
        """
        start_time = time.time()
        
        try:
            # Validate query first
            if not await self.validate_query(request):
                return RetrievalResult(
                    success=False,
                    error=ValueError("Invalid query request"),
                    processing_time_seconds=time.time() - start_time,
                )
            
            # Configure retriever with request parameters
            retriever = VectorIndexRetriever(
                index=self.vector_index,
                similarity_top_k=request.similarity_top_k,
                vector_store_query_mode=request.query_mode,
            )
            
            # Perform retrieval
            nodes_with_scores = await retriever.aretrieve(request.query)
            
            # Apply similarity filtering if specified
            filtered_nodes = self._apply_similarity_filter(
                nodes_with_scores, request.similarity_threshold
            )
            
            # Convert to our RetrievedNode format
            retrieved_nodes = self._convert_nodes_to_retrieved_nodes(filtered_nodes)
            
            processing_time = time.time() - start_time
            
            return RetrievalResult(
                success=True,
                chunks=retrieved_nodes,
                query_metadata={
                    "original_query": request.query,
                    "similarity_top_k": request.similarity_top_k,
                    "query_mode": request.query_mode,
                    "similarity_threshold": request.similarity_threshold,
                    "namespace": request.namespace,
                },
                total_nodes_found=len(retrieved_nodes),
                processing_time_seconds=processing_time,
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return RetrievalResult(
                success=False,
                error=e,
                query_metadata={
                    "original_query": request.query,
                    "similarity_top_k": request.similarity_top_k,
                    "query_mode": request.query_mode,
                },
                processing_time_seconds=processing_time,
            )
    
    async def validate_query(self, request: QueryRequest) -> bool:
        """Validate if the query request can be processed.
        
        Args:
            request: The query request to validate
            
        Returns:
            True if the query is valid and can be processed, False otherwise
        """
        try:
            # Check if query is not empty
            if not request.query or not request.query.strip():
                return False
            
            # Check if similarity_top_k is reasonable
            if request.similarity_top_k <= 0 or request.similarity_top_k > 1000:
                return False
            
            # Check similarity threshold if provided
            if request.similarity_threshold is not None:
                if not (0.0 <= request.similarity_threshold <= 1.0):
                    return False
            
            # Check query mode
            if request.query_mode not in ["default", "sparse", "hybrid"]:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _apply_similarity_filter(
        self, 
        nodes_with_scores: List[NodeWithScore], 
        threshold: Optional[float]
    ) -> List[NodeWithScore]:
        """Apply similarity threshold filtering to retrieved nodes.
        
        Args:
            nodes_with_scores: Raw nodes with similarity scores from retriever
            threshold: Minimum similarity threshold (if specified)
            
        Returns:
            Filtered list of nodes
        """
        if threshold is None:
            return nodes_with_scores
        
        filtered_nodes = []
        for node_with_score in nodes_with_scores:
            score = node_with_score.score
            if score is not None and score >= threshold:
                filtered_nodes.append(node_with_score)
        
        return filtered_nodes
    
    def _convert_nodes_to_retrieved_nodes(
        self, nodes_with_scores: List[NodeWithScore]
    ) -> List[RetrievedChunk]:
        """Convert LlamaIndex NodeWithScore objects to our RetrievedNode format.
        
        Args:
            nodes_with_scores: LlamaIndex nodes with similarity scores
            
        Returns:
            List of RetrievedNode objects with our abstraction
        """
        retrieved_nodes = []
        
        for node_with_score in nodes_with_scores:
            node = node_with_score.node
            score = node_with_score.score or 0.0
            
            # Extract content and metadata
            content = node.get_content()
            metadata = dict(node.metadata) if node.metadata else {}
            
            # Create our RetrievedNode
            retrieved_node = RetrievedChunk(
                node_id=node.node_id,
                content=content,
                similarity_score=score,
                metadata=metadata,
            )
            
            retrieved_nodes.append(retrieved_node)
        
        return retrieved_nodes 