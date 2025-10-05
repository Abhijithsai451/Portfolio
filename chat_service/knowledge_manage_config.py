# knowledge_manager.py
import argparse
import json
from datetime import datetime
from backend.main import load_knowledge_base, chunk_text


def export_knowledge_stats():
    knowledge = load_knowledge_base("knowledge_base.txt")
    chunks = chunk_text(knowledge)

    stats = {
        "last_updated": datetime.now().isoformat(),
        "total_characters": len(knowledge),
        "total_words": len(knowledge.split()),
        "total_chunks": len(chunks),
        "chunk_sizes": [len(chunk) for chunk in chunks],
        "sections": extract_sections(knowledge)
    }

    with open("knowledge_stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    print("Knowledge base statistics exported!")


def extract_sections(text):
    sections = {}
    current_section = "General"

    for line in text.split('\n'):
        if line.strip().startswith('## '):
            current_section = line.strip()[3:]
            sections[current_section] = []
        elif line.strip() and not line.strip().startswith('#'):
            sections.setdefault(current_section, []).append(line.strip())

    return {k: len(v) for k, v in sections.items()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage knowledge base")
    parser.add_argument("--stats", action="store_true", help="Export statistics")

    args = parser.parse_args()

    if args.stats:
        export_knowledge_stats()
