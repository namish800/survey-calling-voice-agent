import asyncio
from dataclasses import dataclass
import logging
import os

from kb_retriever import RetrievalResult
from kb_retriever.models.retrieval import (
    EmbeddingConfig,
    QueryRequest,
    RetrievalConfig,
    VectorStoreConfig,
)
from kb_retriever.llamaindex_document_retrieval import LlamaIndexDocumentRetrievalFromPinecone
from pinecone import Pinecone
from llama_index.vector_stores.pinecone import PineconeVectorStore

from universalagent.tools.tool_holder import ToolHolder

from livekit.agents import RunContext

logger = logging.getLogger(__name__)


@dataclass
class RAGToolConfig:
    """Configuration for RAG system"""

    openai_api_key: str
    pinecone_api_key: str
    index_name: str
    namespace: str = "demo"
    embedding_model: str = "text-embedding-ada-002"
    similarity_top_k: int = 5
    similarity_threshold: float = 0.7


class LlamaIndexPineconeRagTool:
    def __init__(self, config: RAGToolConfig):
        self.config = config
        self.retrieval_pipeline = None
        # Initialize retrieval pipeline
        self._init_retrieval_pipeline()

    def _init_retrieval_pipeline(self):
        try:
            # Configuration
            retrieval_config = RetrievalConfig(
                embedding_config=EmbeddingConfig(
                    api_key=self.config.openai_api_key,
                    model_name=self.config.embedding_model,
                )
            )

            # Initialize Pinecone vector store
            pc = Pinecone(api_key=self.config.pinecone_api_key)
            pinecone_index = pc.Index(self.config.index_name)
            vector_store = PineconeVectorStore(
                pinecone_index=pinecone_index, namespace=self.config.namespace
            )

            # Initialize retrieval pipeline
            self.retrieval_pipeline = LlamaIndexDocumentRetrievalFromPinecone(
                retrieval_config, vector_store
            )

            logger.info("RAG pipeline initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {e}")
            self.retrieval_pipeline = None

    async def retrieve(self, query: str):
        """Search the knowledge base and return relevant content"""

        if not self.retrieval_pipeline:
            logger.error("RAG pipeline not initialized")
            return "I'm sorry, I'm unable to access the knowledge base right now."

        try:
            logger.info(f"Searching knowledge base for: {query}")

            # Create query request
            query_request = QueryRequest(
                query=query,
                similarity_top_k=self.config.similarity_top_k,
                similarity_threshold=self.config.similarity_threshold,
            )

            # Retrieve relevant content
            result: RetrievalResult = await self.retrieval_pipeline.retrieve(query_request)

            if not result.chunks:
                return (
                    "I couldn't find specific information about that topic in our knowledge base."
                )

            # Combine results into a coherent response
            content_parts = []
            for i, node in enumerate(result.chunks, 1):
                # Add some context about the source
                content_parts.append(f"From our knowledge base: {node.content.strip()}")

            combined_content = "\n\n".join(content_parts)

            logger.info(f"Found {len(result.chunks)} relevant chunks")
            return combined_content

        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return "I'm having trouble accessing that information right now. Is there anything else I can help you with?"

    def get_rag_tool(self):
        description = """
        Search the knowledge base and return relevant content

        Args:
            query: The query to search the knowledge base with

        Returns:
            The relevant content from the knowledge base
        """

        # Create a standalone function that captures the method
        async def search_knowledge_base(context: RunContext, query: str):
            return await self.retrieve(query)

        usage_instructions_llm = """
        Use this tool to search the knowledge base for relevant content. Always mention that you are using the knowledge base to answer the question.
        If you do not have the information, say you do not know. Do not make up information.
        Use this tool to answer the questions that are related to the knowledge base.
        Do not answer questions from your general knowledge use this tool to answer questions.
        """

        return ToolHolder(
            search_knowledge_base,
            name="search_knowledge_base",
            description=description,
            usage_instructions_llm=usage_instructions_llm,
        )
