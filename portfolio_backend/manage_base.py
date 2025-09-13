#!/usr/bin/env python3
"""
Utility to manage and update the knowledge base
"""

import argparse

from main import load_knowledge_base, chunk_text


def show_stats():
    """Show knowledge base statistics"""
    knowledge = load_knowledge_base("knowledge_base.txt")
    chunks = chunk_text(knowledge)

    print("Knowledge Base Statistics:")
    print(f"Total characters: {len(knowledge)}")
    print(f"Number of chunks: {len(chunks)}")
    print(f"Average chunk length: {sum(len(c) for c in chunks) / len(chunks):.1f} characters")
    print("\nFirst few chunks:")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n--- Chunk {i + 1} ({len(chunk)} chars) ---")
        print(chunk[:200] + "..." if len(chunk) > 200 else chunk)


def update_knowledge(new_content: str):
    """Update the knowledge base file"""
    try:
        with open("knowledge_base.txt", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Knowledge base updated successfully!")
        show_stats()
    except Exception as e:
        print(f"Error updating knowledge base: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage knowledge base")
    parser.add_argument("--stats", action="store_true", help="Show knowledge base statistics")
    parser.add_argument("--update", help="Update knowledge base with new content")

    args = parser.parse_args()

    if args.stats:
        show_stats()
    elif args.update:
        update_knowledge(args.update)
    else:
        print("Please specify an action: --stats or --update")
