from pathlib import Path
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from dataclasses import dataclass

@dataclass
class CodeChunk:
    id: str              # Unique ID: "file.py::function_name"
    file_path: str       # Relative path
    content: str         # The actual code
    start_line: int      # Where in file
    symbol_name: str     # Function/class name or "module"
    symbol_type: str     # "function", "class", "module"

class VectorStore:
    def __init__(self, persist_dir: Path):
        self.persist_dir = persist_dir
        
        # Load embedding model (local, no API calls)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create/connect to ChromaDB
        self.client = chromadb.Client(Settings(
            persist_directory=str(persist_dir),
            is_persistent=True
        ))
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="code_index",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_file(self, file_content) -> List[str]:
        """Index a file: split into chunks, embed, store"""
        chunks = self._chunk_file(file_content)
        
        if not chunks:
            return []
        
        # Prepare for ChromaDB
        ids = [c.id for c in chunks]
        documents = [c.content for c in chunks]
        metadatas = [{
            "file_path": c.file_path,
            "start_line": c.start_line,
            "symbol_name": c.symbol_name,
            "symbol_type": c.symbol_type
        } for c in chunks]
        
        # Generate embeddings and store
        embeddings = self.model.encode(documents).tolist()
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        return ids
    
    def _chunk_file(self, file_content) -> List[CodeChunk]:
        """Split file into chunks: one per symbol, plus full file"""
        chunks = []
        base_id = str(file_content.path).replace("/", "::")
        
        # Add each symbol as chunk
        if file_content.symbols:
            for sym in file_content.symbols:
                # Extract symbol's code from full content
                lines = file_content.content.splitlines()
                symbol_lines = lines[sym.start_line-1:sym.end_line]
                symbol_code = "\n".join(symbol_lines)
                
                chunk = CodeChunk(
                    id=f"{base_id}::{sym.name}",
                    file_path=str(file_content.path),
                    content=symbol_code,
                    start_line=sym.start_line,
                    symbol_name=sym.name,
                    symbol_type=sym.type
                )
                chunks.append(chunk)
        
        # Also add full file as "module" chunk
        chunks.append(CodeChunk(
            id=f"{base_id}::module",
            file_path=str(file_content.path),
            content=file_content.content[:2000],  # First 2000 chars
            start_line=1,
            symbol_name="module",
            symbol_type="module"
        ))
        
        return chunks
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search code by natural language query"""
        # Embed query
        query_embedding = self.model.encode(query).tolist()
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        formatted = []
        for i in range(len(results['ids'][0])):
            formatted.append({
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })
        
        return formatted
    
    def persist(self):
        """Save to disk"""
        # ChromaDB auto-persists, but explicit call ensures it
        pass  