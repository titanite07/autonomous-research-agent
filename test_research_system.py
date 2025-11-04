"""Quick test of AutoGenResearchSystem"""
import os
from dotenv import load_dotenv
from autogen_research_system import AutoGenResearchSystem

# Load environment
load_dotenv()

print("=" * 60)
print("Testing AutoGenResearchSystem")
print("=" * 60)

# Initialize system
system = AutoGenResearchSystem()

# Test search
print("\n🔍 Testing search for 'machine learning'...")
result = system.search_papers(
    query="machine learning", 
    max_results=3,
    sources=["arxiv"]  # Just test arXiv for speed
)

print(f"\n📊 Results:")
print(f"   Total papers: {result['total']}")
print(f"   Sources: {result['sources']}")

if result['papers']:
    print(f"\n📄 Sample paper:")
    paper = result['papers'][0]
    print(f"   Title: {paper.get('title', 'N/A')}")
    print(f"   Authors: {', '.join(paper.get('authors', [])[:3])}")
    print(f"   Source: {paper.get('source', 'unknown')}")
    print("\n✅ Search functionality working!")
else:
    print("\n⚠️ No papers found!")

print("=" * 60)
