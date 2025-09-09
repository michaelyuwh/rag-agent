"""
Document ingestion pipeline: parsing, chunking, embedding, and storing.
Handles multiple document formats and integrates with vector store.
"""

import os
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Document parsing imports
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# Try to import newer HuggingFace embeddings, fallback to community version
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_chroma import Chroma

# File type specific parsers
try:
    import pypdf
    from pypdf import PdfReader
except ImportError:
    pypdf = None

try:
    import docx2txt
except ImportError:
    docx2txt = None

logger = logging.getLogger(__name__)

class DocumentParser:
    """Handles parsing of different document types."""
    
    @staticmethod
    def parse_text_file(file_path: str) -> str:
        """Parse plain text files."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    @staticmethod
    def parse_pdf(file_path: str) -> str:
        """Parse PDF files."""
        if not pypdf:
            raise ImportError("pypdf package required for PDF parsing. Install with: pip install pypdf")
        
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            raise
    
    @staticmethod
    def parse_docx(file_path: str) -> str:
        """Parse Word documents."""
        if not docx2txt:
            raise ImportError("docx2txt package required for Word parsing. Install with: pip install docx2txt")
        
        try:
            return docx2txt.process(file_path)
        except Exception as e:
            logger.error(f"Error parsing DOCX {file_path}: {e}")
            raise
    
    @staticmethod
    def parse_csv(file_path: str) -> str:
        """Parse CSV files."""
        try:
            df = pd.read_csv(file_path)
            # Convert to a readable text format
            return f"CSV File Content:\n{df.to_string()}"
        except Exception as e:
            logger.error(f"Error parsing CSV {file_path}: {e}")
            raise
    
    @staticmethod
    def parse_excel(file_path: str) -> str:
        """Parse Excel files."""
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            content = "Excel File Content:\n"
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                content += f"\n--- Sheet: {sheet_name} ---\n"
                content += df.to_string() + "\n"
            
            return content
        except Exception as e:
            logger.error(f"Error parsing Excel {file_path}: {e}")
            raise
    
    @classmethod
    def parse_file(cls, file_path: str) -> str:
        """Parse a file based on its extension."""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        parsers = {
            '.txt': cls.parse_text_file,
            '.md': cls.parse_text_file,
            '.py': cls.parse_text_file,
            '.js': cls.parse_text_file,
            '.html': cls.parse_text_file,
            '.css': cls.parse_text_file,
            '.json': cls.parse_text_file,
            '.xml': cls.parse_text_file,
            '.yaml': cls.parse_text_file,
            '.yml': cls.parse_text_file,
            '.pdf': cls.parse_pdf,
            '.docx': cls.parse_docx,
            '.csv': cls.parse_csv,
            '.xlsx': cls.parse_excel,
            '.xls': cls.parse_excel,
        }
        
        parser = parsers.get(extension)
        if not parser:
            # Default to text parser for unknown types
            logger.warning(f"Unknown file type {extension}, treating as text")
            parser = cls.parse_text_file
        
        return parser(str(file_path))

class DocumentIngestion:
    """Handles document ingestion pipeline."""
    
    def __init__(
        self,
        vector_store_path: str = "data/vector_store",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        self.vector_store_path = Path(vector_store_path)
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},  # Use CPU for compatibility
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Initialize or load vector store
        self.vector_store = self._init_vector_store()
        
        # Document metadata storage
        self.metadata_file = self.vector_store_path / "document_metadata.json"
        self.metadata = self._load_metadata()
    
    def _init_vector_store(self) -> Chroma:
        """Initialize the Chroma vector store."""
        try:
            # Try to load existing vector store
            vector_store = Chroma(
                persist_directory=str(self.vector_store_path),
                embedding_function=self.embeddings
            )
            logger.info(f"Loaded existing vector store from {self.vector_store_path}")
            return vector_store
        except Exception as e:
            logger.info(f"Creating new vector store at {self.vector_store_path}")
            # Create new vector store
            vector_store = Chroma(
                persist_directory=str(self.vector_store_path),
                embedding_function=self.embeddings
            )
            return vector_store
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load document metadata from file."""
        if self.metadata_file.exists():
            try:
                import json
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
        return {}
    
    def _save_metadata(self):
        """Save document metadata to file."""
        try:
            import json
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate hash for file content."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def ingest_document(
        self,
        file_path: str,
        original_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingest a document into the vector store.
        
        Args:
            file_path: Path to the file to ingest
            original_name: Original filename (for temp files)
            
        Returns:
            Dictionary with ingestion results
        """
        file_path = Path(file_path)
        document_name = original_name or file_path.name
        
        try:
            # Check if file exists
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Get file info
            file_size = file_path.stat().st_size
            file_hash = self._get_file_hash(str(file_path))
            
            # Check if already processed
            if file_hash in self.metadata:
                logger.info(f"Document {document_name} already processed (same hash)")
                return {
                    "status": "skipped",
                    "message": "Document already exists",
                    "document_name": document_name
                }
            
            # Parse document
            logger.info(f"Parsing document: {document_name}")
            content = DocumentParser.parse_file(str(file_path))
            
            if not content.strip():
                raise ValueError("Document appears to be empty or could not be parsed")
            
            # Split into chunks
            logger.info(f"Splitting document into chunks: {document_name}")
            chunks = self.text_splitter.split_text(content)
            
            # Create Document objects with metadata
            documents = []
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": document_name,
                        "chunk_id": i,
                        "total_chunks": len(chunks),
                        "file_hash": file_hash,
                        "file_size": file_size,
                        "ingestion_time": datetime.now().isoformat(),
                        "file_type": file_path.suffix.lower()
                    }
                )
                documents.append(doc)
            
            # Add to vector store
            logger.info(f"Adding {len(documents)} chunks to vector store")
            self.vector_store.add_documents(documents)
            
            # Save document metadata
            self.metadata[file_hash] = {
                "document_name": document_name,
                "file_size": file_size,
                "chunk_count": len(chunks),
                "ingestion_time": datetime.now().isoformat(),
                "file_type": file_path.suffix.lower(),
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            }
            
            self._save_metadata()
            
            # Persist vector store
            self.vector_store.persist()
            
            logger.info(f"Successfully ingested document: {document_name}")
            
            return {
                "status": "success",
                "message": f"Successfully processed {document_name}",
                "document_name": document_name,
                "chunk_count": len(chunks),
                "file_size": file_size
            }
            
        except Exception as e:
            logger.error(f"Error ingesting document {document_name}: {e}")
            return {
                "status": "error",
                "message": f"Error processing {document_name}: {str(e)}",
                "document_name": document_name
            }
    
    def ingest_multiple_documents(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Ingest multiple documents."""
        results = []
        for file_path in file_paths:
            result = self.ingest_document(file_path)
            results.append(result)
        return results
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about ingested documents."""
        total_documents = len(self.metadata)
        total_chunks = sum(doc.get("chunk_count", 0) for doc in self.metadata.values())
        total_size = sum(doc.get("file_size", 0) for doc in self.metadata.values())
        
        # Get file type distribution
        file_types = {}
        for doc in self.metadata.values():
            file_type = doc.get("file_type", "unknown")
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        return {
            "total_documents": total_documents,
            "total_chunks": total_chunks,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types": file_types,
            "documents": list(self.metadata.values())
        }
    
    def remove_document(self, file_hash: str) -> bool:
        """Remove a document from the vector store."""
        try:
            if file_hash in self.metadata:
                # Note: Chroma doesn't have easy document removal by metadata
                # This would require more complex implementation
                # For now, we'll just remove from metadata
                del self.metadata[file_hash]
                self._save_metadata()
                logger.info(f"Removed document metadata for hash: {file_hash}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing document: {e}")
            return False
    
    def clear_all_documents(self):
        """Clear all documents from the vector store."""
        try:
            # Delete the entire vector store directory and recreate
            import shutil
            if self.vector_store_path.exists():
                shutil.rmtree(self.vector_store_path)
            
            # Recreate directory and vector store
            self.vector_store_path.mkdir(parents=True, exist_ok=True)
            self.vector_store = self._init_vector_store()
            
            # Clear metadata
            self.metadata = {}
            self._save_metadata()
            
            logger.info("Cleared all documents from vector store")
        except Exception as e:
            logger.error(f"Error clearing documents: {e}")
            raise

import os
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Document parsers
try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import docx2txt
except ImportError:
    docx2txt = None

try:
    import pandas as pd
except ImportError:
    pd = None

# LangChain components
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_chroma import Chroma
except ImportError:
    # Will be handled gracefully
    pass

logger = logging.getLogger(__name__)

class DocumentParser:
    """Handles parsing of various document formats."""
    
    @staticmethod
    def parse_text(file_path: str) -> str:
        """Parse plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
                
    @staticmethod
    def parse_pdf(file_path: str) -> str:
        """Parse PDF file."""
        if not pypdf:
            raise ImportError("pypdf package required for PDF parsing")
            
        text = ""
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = pypdf.PdfReader(f)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            raise
            
        return text
        
    @staticmethod 
    def parse_docx(file_path: str) -> str:
        """Parse Word document."""
        if not docx2txt:
            raise ImportError("docx2txt package required for DOCX parsing")
            
        try:
            return docx2txt.process(file_path)
        except Exception as e:
            logger.error(f"Error parsing DOCX {file_path}: {e}")
            raise
            
    @staticmethod
    def parse_csv(file_path: str) -> str:
        """Parse CSV file."""
        if not pd:
            raise ImportError("pandas package required for CSV parsing")
            
        try:
            df = pd.read_csv(file_path)
            # Convert to readable text format
            return df.to_string(index=False)
        except Exception as e:
            logger.error(f"Error parsing CSV {file_path}: {e}")
            raise
            
    @staticmethod
    def parse_excel(file_path: str) -> str:
        """Parse Excel file."""
        if not pd:
            raise ImportError("pandas package required for Excel parsing")
            
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            text_parts = []
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                text_parts.append(f"Sheet: {sheet_name}\n")
                text_parts.append(df.to_string(index=False))
                text_parts.append("\n\n")
                
            return "".join(text_parts)
        except Exception as e:
            logger.error(f"Error parsing Excel {file_path}: {e}")
            raise

class DocumentIngestion:
    """Main document ingestion pipeline."""
    
    SUPPORTED_EXTENSIONS = {
        '.txt': 'text',
        '.md': 'text', 
        '.py': 'text',
        '.js': 'text',
        '.ts': 'text',
        '.html': 'text',
        '.css': 'text',
        '.json': 'text',
        '.yml': 'text',
        '.yaml': 'text',
        '.xml': 'text',
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.csv': 'csv',
        '.xlsx': 'excel',
        '.xls': 'excel'
    }
    
    def __init__(self, vector_store_path: str = "data/vector_store", 
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.vector_store_path = vector_store_path
        self.embedding_model_name = embedding_model
        self.parser = DocumentParser()
        
        # Initialize text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Initialize embedding model
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=embedding_model,
                model_kwargs={'device': 'cpu'}  # Use CPU for cross-platform compatibility
            )
        except Exception as e:
            logger.error(f"Error initializing embedding model: {e}")
            self.embeddings = None
            
        # Initialize vector store
        self._init_vector_store()
        
    def _init_vector_store(self):
        """Initialize the vector store."""
        try:
            os.makedirs(self.vector_store_path, exist_ok=True)
            
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
            
    def is_supported(self, file_path: str) -> bool:
        """Check if file type is supported."""
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS
        
    def get_file_type(self, file_path: str) -> Optional[str]:
        """Get the file type for parsing."""
        ext = Path(file_path).suffix.lower()
        return self.SUPPORTED_EXTENSIONS.get(ext)
        
    def parse_document(self, file_path: str) -> str:
        """Parse a document based on its type."""
        file_type = self.get_file_type(file_path)
        
        if not file_type:
            raise ValueError(f"Unsupported file type: {Path(file_path).suffix}")
            
        try:
            if file_type == 'text':
                return self.parser.parse_text(file_path)
            elif file_type == 'pdf':
                return self.parser.parse_pdf(file_path)
            elif file_type == 'docx':
                return self.parser.parse_docx(file_path)
            elif file_type == 'csv':
                return self.parser.parse_csv(file_path)
            elif file_type == 'excel':
                return self.parser.parse_excel(file_path)
            else:
                raise ValueError(f"Unknown file type: {file_type}")
                
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            raise
            
    def chunk_text(self, text: str, file_name: str) -> List[Document]:
        """Split text into chunks."""
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            # Create Document objects with metadata
            documents = []
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "file_name": file_name,
                        "chunk_id": i,
                        "total_chunks": len(chunks),
                        "upload_date": datetime.now().isoformat(),
                        "file_hash": hashlib.md5(text.encode()).hexdigest()[:8]
                    }
                )
                documents.append(doc)
                
            return documents
            
        except Exception as e:
            logger.error(f"Error chunking text for {file_name}: {e}")
            raise
            
    def ingest_document(self, file_path: str, file_name: Optional[str] = None) -> Dict[str, Any]:
        """Ingest a single document into the vector store."""
        if not self.vector_store:
            raise RuntimeError("Vector store not initialized")
            
        if not file_name:
            file_name = Path(file_path).name
            
        try:
            # Check file size (limit to 50MB as per requirements)
            file_size = os.path.getsize(file_path)
            if file_size > 50 * 1024 * 1024:  # 50MB
                raise ValueError("File too large (max 50MB)")
                
            # Parse document
            logger.info(f"Parsing document: {file_name}")
            text = self.parse_document(file_path)
            
            if not text.strip():
                raise ValueError("No text content extracted from document")
                
            # Chunk text
            logger.info(f"Chunking document: {file_name}")
            documents = self.chunk_text(text, file_name)
            
            # Add to vector store
            logger.info(f"Adding {len(documents)} chunks to vector store")
            ids = self.vector_store.add_documents(documents)
            
            # Return ingestion summary
            result = {
                "file_name": file_name,
                "file_size": file_size,
                "num_chunks": len(documents),
                "chunk_ids": ids,
                "upload_date": datetime.now().isoformat(),
                "status": "success"
            }
            
            logger.info(f"Successfully ingested {file_name}: {len(documents)} chunks")
            return result
            
        except Exception as e:
            logger.error(f"Error ingesting {file_name}: {e}")
            return {
                "file_name": file_name,
                "status": "error",
                "error": str(e)
            }
            
    def ingest_text(self, text: str, title: str = "user_text") -> Dict[str, Any]:
        """Ingest raw text (e.g., from chat input)."""
        if not self.vector_store:
            raise RuntimeError("Vector store not initialized")
            
        try:
            # Chunk text
            documents = self.chunk_text(text, title)
            
            # Add to vector store  
            ids = self.vector_store.add_documents(documents)
            
            result = {
                "file_name": title,
                "num_chunks": len(documents),
                "chunk_ids": ids,
                "upload_date": datetime.now().isoformat(),
                "status": "success"
            }
            
            logger.info(f"Successfully ingested text '{title}': {len(documents)} chunks")
            return result
            
        except Exception as e:
            logger.error(f"Error ingesting text '{title}': {e}")
            return {
                "file_name": title,
                "status": "error", 
                "error": str(e)
            }
            
    def get_document_list(self) -> List[Dict[str, Any]]:
        """Get list of all documents in the vector store."""
        if not self.vector_store:
            return []
            
        try:
            # Get all documents
            results = self.vector_store.get()
            
            if not results or not results.get('metadatas'):
                return []
                
            # Group by file name and aggregate metadata
            docs_by_file = {}
            
            for metadata in results['metadatas']:
                file_name = metadata.get('file_name', 'unknown')
                
                if file_name not in docs_by_file:
                    docs_by_file[file_name] = {
                        'file_name': file_name,
                        'chunk_count': 0,
                        'upload_date': metadata.get('upload_date', 'unknown'),
                        'file_hash': metadata.get('file_hash', 'unknown')
                    }
                    
                docs_by_file[file_name]['chunk_count'] += 1
                
            return list(docs_by_file.values())
            
        except Exception as e:
            logger.error(f"Error getting document list: {e}")
            return []
            
    def delete_document(self, file_name: str) -> bool:
        """Delete all chunks of a document from the vector store."""
        if not self.vector_store:
            return False
            
        try:
            # Get all document IDs for this file
            results = self.vector_store.get()
            
            if not results or not results.get('metadatas'):
                return False
                
            ids_to_delete = []
            for i, metadata in enumerate(results['metadatas']):
                if metadata.get('file_name') == file_name:
                    ids_to_delete.append(results['ids'][i])
                    
            if ids_to_delete:
                self.vector_store.delete(ids=ids_to_delete)
                logger.info(f"Deleted {len(ids_to_delete)} chunks for {file_name}")
                return True
            else:
                logger.warning(f"No chunks found for {file_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document {file_name}: {e}")
            return False
            
    def clear_all_documents(self) -> bool:
        """Clear all documents from the vector store."""
        if not self.vector_store:
            return False
            
        try:
            # Get all document IDs
            results = self.vector_store.get()
            
            if results and results.get('ids'):
                self.vector_store.delete(ids=results['ids'])
                logger.info(f"Cleared {len(results['ids'])} chunks from vector store")
                
            return True
            
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            return False
