"""
Chat API routes
Provides AI assistant functionality for research guidance
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
from groq import Groq

router = APIRouter()

# Initialize Groq client
groq_api_key = os.getenv('GROQ_API_KEY')
if not groq_api_key:
    print("⚠️ Warning: GROQ_API_KEY not found. Chat functionality will be limited.")
    groq_client = None
else:
    groq_client = Groq(api_key=groq_api_key)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = None


SYSTEM_PROMPT = """You are a helpful AI research assistant for an academic paper search system. 
Your role is to help users:

1. **Craft Better Search Queries**: Help refine vague queries into precise academic search terms
2. **Understand Research Topics**: Explain complex concepts and suggest related areas
3. **Interpret Results**: Help users understand paper relevance scores and citations
4. **Research Guidance**: Suggest keywords, related topics, and research directions
5. **Paper Proposals**: Guide users in structuring their research proposals and literature reviews

Guidelines:
- Be concise and actionable
- Suggest specific search terms when relevant
- Explain academic concepts clearly
- Recommend reputable sources (arXiv, IEEE, ACM, etc.)
- Help with research methodology questions
- Provide paper structure suggestions

Keep responses focused on academic research and paper discovery."""


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with AI assistant for research guidance
    
    - **message**: User's message
    - **conversation_history**: Previous conversation context
    
    Returns AI-generated response with optional suggestions
    """
    
    if not groq_client:
        return ChatResponse(
            response="I apologize, but the AI chat service is currently unavailable. Please try again later or contact support.",
            suggestions=None
        )
    
    try:
        # Build messages for Groq API
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
        # Add conversation history (limit to last 10 messages for context window)
        if request.conversation_history:
            for msg in request.conversation_history[-10:]:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        # Call Groq API
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Fast and efficient model
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            top_p=0.9,
        )
        
        ai_response = response.choices[0].message.content
        
        # Generate suggestions based on context
        suggestions = []
        message_lower = request.message.lower()
        
        if any(word in message_lower for word in ['search', 'find', 'query', 'papers']):
            suggestions = [
                "Try adding year ranges like '2020-2024'",
                "Include specific methodologies or techniques",
                "Combine with domain names (NLP, CV, ML)"
            ]
        elif any(word in message_lower for word in ['proposal', 'research', 'topic']):
            suggestions = [
                "Start with a literature review",
                "Define clear research questions",
                "Identify gaps in current research"
            ]
        elif any(word in message_lower for word in ['help', 'how', 'what']):
            suggestions = [
                "Ask about specific search queries",
                "Request paper recommendations",
                "Get research methodology advice"
            ]
        
        return ChatResponse(
            response=ai_response,
            suggestions=suggestions if suggestions else None
        )
        
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}"
        )


@router.get("/chat/suggestions")
async def get_suggestions():
    """
    Get common research assistant suggestions
    
    Returns helpful prompts users can ask
    """
    return {
        "categories": [
            {
                "name": "Search Help",
                "suggestions": [
                    "How do I search for papers on transformer models?",
                    "What are good keywords for machine learning research?",
                    "Help me refine my query about deep learning",
                ]
            },
            {
                "name": "Research Guidance",
                "suggestions": [
                    "How should I structure my literature review?",
                    "What makes a good research proposal?",
                    "How do I identify research gaps?",
                ]
            },
            {
                "name": "Paper Understanding",
                "suggestions": [
                    "What does citation count indicate?",
                    "How do I evaluate paper relevance?",
                    "What are impact factors?",
                ]
            },
            {
                "name": "Topic Exploration",
                "suggestions": [
                    "What are current trends in AI research?",
                    "Suggest related topics to BERT",
                    "What are foundational papers in NLP?",
                ]
            }
        ]
    }
