import os
import chromadb
from chromadb.utils import embedding_functions

class VectorStoreService:
    """Service to handle vector database storage (ChromaDB) for RAG and long-term memory."""
    
    def __init__(self, persist_dir: str = None):
        if not persist_dir:
            # Save inside the backend directory of the project
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            persist_dir = os.path.join(base_dir, "chroma_db")
        
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Use ONNX-based all-MiniLM-L6-v2 running locally (free, offline, no API keys)
        self.embedding_fn = embedding_functions.ONNXMiniLM_L6_V2()
        
        # Collections for code chunks and requirements/doc history
        self.code_collection = self.client.get_or_create_collection(
            name="generated_code",
            embedding_function=self.embedding_fn
        )
        self.doc_collection = self.client.get_or_create_collection(
            name="generated_docs",
            embedding_function=self.embedding_fn
        )

    def add_code_chunk(self, job_id: str, file_path: str, content: str):
        """Chunk code and add to the vector store."""
        if not content.strip():
            return
        
        # Simple line-based chunking for code (every 30 lines with 5 lines overlap)
        lines = content.splitlines()
        chunk_size = 30
        overlap = 5
        
        idx = 0
        while idx < len(lines):
            chunk_lines = lines[idx : idx + chunk_size]
            chunk_text = "\n".join(chunk_lines)
            clean_path = file_path.replace('/', '_').replace('\\', '_')
            doc_id = f"{job_id}_{clean_path}_{idx}"
            
            self.code_collection.add(
                documents=[chunk_text],
                metadatas=[{"job_id": job_id, "file_path": file_path, "start_line": idx + 1}],
                ids=[doc_id]
            )
            idx += (chunk_size - overlap)

    def add_documentation(self, job_id: str, doc_name: str, content: str):
        """Add documentation sections to the vector store."""
        if not content.strip():
            return
        
        # Chunk docs by paragraph/headers (split by double newline)
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        for idx, para in enumerate(paragraphs):
            doc_id = f"{job_id}_doc_{doc_name}_{idx}"
            self.doc_collection.add(
                documents=[para],
                metadatas=[{"job_id": job_id, "doc_name": doc_name, "chunk_index": idx}],
                ids=[doc_id]
            )

    def search_code(self, query_text: str, job_id: str = None, n_results: int = 3) -> list:
        """Search code chunks matching query, optionally filtered by job_id."""
        where_filter = {"job_id": job_id} if job_id else None
        results = self.code_collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_filter
        )
        # Re-format output as a clean list of dicts
        formatted = []
        if results and results.get("documents"):
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]
            for doc, meta, dist in zip(docs, metas, distances):
                formatted.append({
                    "content": doc,
                    "file_path": meta.get("file_path"),
                    "start_line": meta.get("start_line"),
                    "distance": dist
                })
        return formatted

    def search_docs(self, query_text: str, job_id: str = None, n_results: int = 3) -> list:
        """Search docs matching query, optionally filtered by job_id."""
        where_filter = {"job_id": job_id} if job_id else None
        results = self.doc_collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_filter
        )
        formatted = []
        if results and results.get("documents"):
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]
            for doc, meta, dist in zip(docs, metas, distances):
                formatted.append({
                    "content": doc,
                    "doc_name": meta.get("doc_name"),
                    "distance": dist
                })
        return formatted
