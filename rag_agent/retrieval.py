"""
Query processing and retrieval from vector store.
Handles embedding queries and retrieving relevant document chunks.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    
from langchain_chroma import Chroma
from langchain.schema import Document

logger = logging.getLogger(__name__)

@dataclass
class RetrievalResult:
    """Result from document retrieval."""
    content: str
    metadata: Dict[str, Any]
    score: float
    file_name: str
    chunk_id: int

class DocumentRetrieval:
    """Handles query processing and document retrieval."""
    
    def __init__(self, vector_store_path: str = "data/vector_store",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.vector_store_path = vector_store_path
        self.embedding_model_name = embedding_model
        
        # Initialize embedding model
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=embedding_model,
                model_kwargs={'device': 'cpu'}
            )
        except Exception as e:
            logger.error(f"Error initializing embedding model: {e}")
            self.embeddings = None
            
        # Initialize vector store
        self._init_vector_store()
        
    def _init_vector_store(self):
        """Initialize the vector store for retrieval."""
        try:
            if self.embeddings:
                self.vector_store = Chroma(
                    persist_directory=self.vector_store_path,
                    embedding_function=self.embeddings
                )
            else:
                self.vector_store = None
                
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            self.vector_store = None
            
    def is_available(self) -> bool:
        """Check if retrieval system is available."""
        return self.vector_store is not None and self.embeddings is not None
        
    def retrieve_relevant_docs(self, query: str, k: int = 5, 
                             score_threshold: float = 0.0) -> List[RetrievalResult]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: User query string
            k: Number of documents to retrieve
            score_threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List of RetrievalResult objects
        """
        if not self.is_available():
            logger.error("Retrieval system not available")
            return []
            
        try:
            # Perform similarity search with scores
            docs_and_scores = self.vector_store.similarity_search_with_score(
                query, k=k
            )
            
            results = []
            for doc, score in docs_and_scores:
                # Convert score to similarity (Chroma returns distance, lower is better)
                # Normalize to 0-1 scale where 1 is most similar
                similarity_score = max(0.0, 1.0 - score)
                
                if similarity_score >= score_threshold:
                    result = RetrievalResult(
                        content=doc.page_content,
                        metadata=doc.metadata,
                        score=similarity_score,
                        file_name=doc.metadata.get('file_name', 'unknown'),
                        chunk_id=doc.metadata.get('chunk_id', 0)
                    )
                    results.append(result)
                    
            # Sort by score (highest first)
            results.sort(key=lambda x: x.score, reverse=True)
            
            logger.info(f"Retrieved {len(results)} relevant documents for query")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
            
    def retrieve_by_file(self, file_name: str, limit: int = 10) -> List[RetrievalResult]:
        """
        Retrieve all chunks from a specific file.
        
        Args:
            file_name: Name of the file to retrieve chunks from
            limit: Maximum number of chunks to return
            
        Returns:
            List of RetrievalResult objects
        """
        if not self.is_available():
            return []
            
        try:
            # Get all documents
            all_docs = self.vector_store.get()
            
            if not all_docs or not all_docs.get('metadatas'):
                return []
                
            results = []
            for i, metadata in enumerate(all_docs['metadatas']):
                if metadata.get('file_name') == file_name:
                    if len(results) >= limit:
                        break
                        
                    result = RetrievalResult(
                        content=all_docs['documents'][i],
                        metadata=metadata,
                        score=1.0,  # Not based on similarity
                        file_name=file_name,
                        chunk_id=metadata.get('chunk_id', 0)
                    )
                    results.append(result)
                    
            # Sort by chunk_id to maintain order
            results.sort(key=lambda x: x.chunk_id)
            
            logger.info(f"Retrieved {len(results)} chunks from {file_name}")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving file {file_name}: {e}")
            return []
            
    def get_context_for_query(self, query: str, max_tokens: int = 3000) -> str:
        """
        Get relevant context for a query, formatted for LLM input.
        
        Args:
            query: User query
            max_tokens: Approximate maximum tokens in context
            
        Returns:
            Formatted context string
        """
        # Retrieve relevant documents
        relevant_docs = self.retrieve_relevant_docs(query, k=10)
        
        if not relevant_docs:
            return "No relevant documents found in the knowledge base."
            
        context_parts = []
        total_length = 0
        
        for doc in relevant_docs:
            # Format each document chunk
            chunk_text = f"## From {doc.file_name} (chunk {doc.chunk_id + 1})\n"
            chunk_text += f"Relevance: {doc.score:.2f}\n\n"
            chunk_text += doc.content + "\n\n"
            
            # Estimate token count (rough approximation: 1 token ≈ 4 characters)
            chunk_tokens = len(chunk_text) // 4
            
            if total_length + chunk_tokens > max_tokens:
                break
                
            context_parts.append(chunk_text)
            total_length += chunk_tokens
            
        if context_parts:
            context = "## Relevant Context\n\n" + "".join(context_parts)
            context += f"\n---\n*Retrieved {len(context_parts)} relevant document chunks*"
            return context
        else:
            return "No relevant documents found in the knowledge base."
            
    def search_files(self, search_term: str) -> List[str]:
        """
        Search for files containing a specific term in their name.
        
        Args:
            search_term: Term to search for in file names
            
        Returns:
            List of matching file names
        """
        if not self.is_available():
            return []
            
        try:
            # Get all documents
            all_docs = self.vector_store.get()
            
            if not all_docs or not all_docs.get('metadatas'):
                return []
                
            # Get unique file names that match the search term
            matching_files = set()
            search_lower = search_term.lower()
            
            for metadata in all_docs['metadatas']:
                file_name = metadata.get('file_name', '')
                if search_lower in file_name.lower():
                    matching_files.add(file_name)
                    
            return sorted(list(matching_files))
            
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return []
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        if not self.is_available():
            return {"error": "Vector store not available"}
            
        try:
            # Get all documents
            all_docs = self.vector_store.get()
            
            if not all_docs or not all_docs.get('metadatas'):
                return {
                    "total_chunks": 0,
                    "total_files": 0,
                    "files": []
                }
                
            # Count chunks and files
            files_info = {}
            total_chunks = len(all_docs['metadatas'])
            
            for metadata in all_docs['metadatas']:
                file_name = metadata.get('file_name', 'unknown')
                upload_date = metadata.get('upload_date', 'unknown')
                
                if file_name not in files_info:
                    files_info[file_name] = {
                        'name': file_name,
                        'chunk_count': 0,
                        'upload_date': upload_date
                    }
                    
                files_info[file_name]['chunk_count'] += 1
                
            return {
                "total_chunks": total_chunks,
                "total_files": len(files_info),
                "files": list(files_info.values()),
                "embedding_model": self.embedding_model_name
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}
