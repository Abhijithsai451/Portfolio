import logging

# Initialize Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    tool = PortfolioDocTool()
    data_dir = Path("data")
    
    logger.info(f"Indexing documents from {data_dir}...")
    
    files = list(data_dir.glob("*.txt")) + list(data_dir.glob("*.md"))
    
    for file_path in files:
        logger.info(f"Processing {file_path.name}...")
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
            
    logger.info("Indexing complete!")

if __name__ == "__main__":
    asyncio.run(init_db())
