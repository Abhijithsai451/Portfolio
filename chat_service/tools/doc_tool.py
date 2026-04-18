import os
import logging
from typing import List
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class PortfolioDocTool:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
        self.collection = self.chroma_client.get_or_create_collection("portfolio_knowledge")
        
    async def generate_embedding(self, text: str) -> List[float]:
        try:
            res = self.client.embeddings.create(input=text, model="text-embedding-3-small")
            return res.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return []

    async def search_portfolio(self, query: str, top_k: int = 3) -> str:
        """Searches the portfolio knowledge base for relevant information."""
        try:
            emb = await self.generate_embedding(query)
            if not emb:
                return "Could not generate query embedding."
                
            results = self.collection.query(
                query_embeddings=[emb],
                n_results=top_k
            )
            
            if not results['documents'] or not results['documents'][0]:
                return "No relevant information found in documents."
                
            return "\n\n".join(results['documents'][0])
        except Exception as e:
            logger.error(f"Search error: {e}")
            return f"Error searching documents: {str(e)}"
