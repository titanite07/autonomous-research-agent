"""Simple test for Springer API"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('SPRINGER_API_KEY')
print(f"API Key: {api_key[:10]}...{api_key[-5:]}")

url = "https://api.springernature.com/meta/v2/json"
params = {
    'q': 'machine learning',
    'api_key': api_key,
    's': 1,
    'p': 3
}

print(f"\n🔍 Testing Springer API...")
print(f"URL: {url}")

response = requests.get(url, params=params)
print(f"\n✅ Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    records = data.get('records', [])
    print(f"✅ Found {len(records)} papers")
    
    for i, record in enumerate(records[:3], 1):
        title = record.get('title', 'No title')
        print(f"\n{i}. {title}")
else:
    print(f"❌ Error: {response.text[:200]}")
