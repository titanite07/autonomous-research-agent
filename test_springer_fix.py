"""Test Springer API scraper locally"""
import os
from dotenv import load_dotenv
from scrapers.springer_scraper import SpringerScraper

# Load environment variables
load_dotenv()

# Initialize scraper
api_key = os.getenv('SPRINGER_API_KEY')
print(f"Testing Springer API with key: {api_key[:20]}...")

scraper = SpringerScraper(api_key=api_key)

# Test search
print("\n🔍 Searching for 'machine learning'...")
papers = scraper.search("machine learning", max_results=3)

print(f"\n✅ Found {len(papers)} papers from Springer:\n")

for i, paper in enumerate(papers, 1):
    print(f"{i}. {paper.title}")
    print(f"   Authors: {', '.join(paper.authors[:3])}")
    print(f"   Year: {paper.year or 'N/A'}")
    print(f"   URL: {paper.url}")
    print()

if len(papers) > 0:
    print("✅ Springer API test PASSED!")
else:
    print("❌ Springer API test FAILED - no papers returned")
