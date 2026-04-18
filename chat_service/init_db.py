import os
import asyncio
from pathlib import Path
from chat_service.tools.doc_tool import PortfolioDocTool

async def init_db():
    tool = PortfolioDocTool()
    data_dir = Path("data")
    
    print(f"Indexing documents from {data_dir}...")
    
    files = list(data_dir.glob("*.txt")) + list(data_dir.glob("*.md"))
    
    for file_path in files:
        print(f"Processing {file_path.name}...")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Simple chunking
        chunks = [content[i:i+1000] for i in range(0, len(content), 800)]
        
        for i, chunk in enumerate(chunks):
            emb = await tool.generate_embedding(chunk)
            tool.collection.add(
                documents=[chunk],
                embeddings=[emb],
                ids=[f"{file_path.name}_{i}"]
            )
            
    print("Indexing complete!")

if __name__ == "__main__":
    asyncio.run(init_db())
