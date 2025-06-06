import asyncio
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

# Configuration
config = RetrievalConfig(
    embedding_config=EmbeddingConfig(
        api_key=os.getenv("OPENAI_API_KEY", "your-openai-api-key"),
        model_name="text-embedding-ada-002",
    )
)

vector_store_config=VectorStoreConfig(
    api_key=os.getenv("PINECONE_API_KEY", "your-pinecone-api-key"),
    index_name="llama-integration-example",
    namespace="sarvamV1"
)

def get_pinecone_vs():
    # Initialize Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = "llama-integration-example"
    pinecone_index = pc.Index(index_name)
    vector_store = PineconeVectorStore(
        pinecone_index=pinecone_index,
        namespace="demo"
    )
    return vector_store

vs = get_pinecone_vs()
# Initialize retrieval pipeline
retrieval_pipeline = LlamaIndexDocumentRetrievalFromPinecone(config, vs)
    

async def retrieve_chunk(msg: str):
    """Demonstrate basic retrieval functionality."""
    
    print("Message: ", msg)
    
    # Create a query request
    query_request = QueryRequest(
        query=msg,
        similarity_top_k=5,
        similarity_threshold=0.7,
    )

    result: RetrievalResult = await retrieval_pipeline.retrieve(query_request)
    result_str = ""
    
    for node in result.chunks:
        result_str += node.content
        result_str += "\n"

    return result_str


print(asyncio.run(retrieve_chunk("What is sarvam-m?")))