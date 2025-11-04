"""Test if GROQ API key is valid"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")

print("=" * 50)
print("GROQ API KEY TEST")
print("=" * 50)
print(f"Key found: {bool(groq_key)}")
if groq_key:
    print(f"Key format: {groq_key[:10]}...{groq_key[-10:]}")
    print(f"Key length: {len(groq_key)}")
    print(f"Starts with 'gsk_': {groq_key.startswith('gsk_')}")
    
    # Try to make a simple API call
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        
        print("\n🔄 Testing API call...")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say 'Hello'"}],
            max_tokens=10
        )
        print("✅ API call successful!")
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ API call failed: {e}")
else:
    print("❌ No GROQ_API_KEY found in environment!")
print("=" * 50)
