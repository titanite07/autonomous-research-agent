"""
LLM Configuration - Supports OpenAI, Ollama, Groq, OpenRouter, and other providers
"""
import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama  # Updated import
from langchain_groq import ChatGroq  # Re-enabled - compatible with langchain-core 1.0.1
import logging

logger = logging.getLogger(__name__)


class LLMProvider:
    """Factory for creating LLM instances"""
    
    SUPPORTED_PROVIDERS = ["openai", "ollama", "groq", "openrouter"]
    
    @staticmethod
    def create_llm(
        provider: str = "ollama",
        model: Optional[str] = None,
        temperature: float = 0.5,
        **kwargs
    ):
        """
        Create an LLM instance
        
        Args:
            provider: Provider name (openai, ollama)
            model: Model name (provider-specific)
            temperature: Generation temperature
            **kwargs: Additional provider-specific arguments
            
        Returns:
            LLM instance compatible with LangChain
        """
        provider = provider.lower()
        
        if provider == "openai":
            return LLMProvider._create_openai(model, temperature, **kwargs)
        elif provider == "ollama":
            return LLMProvider._create_ollama(model, temperature, **kwargs)
        elif provider == "groq":
            return LLMProvider._create_groq(model, temperature, **kwargs)
        elif provider == "openrouter":
            return LLMProvider._create_openrouter(model, temperature, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}. Choose from {LLMProvider.SUPPORTED_PROVIDERS}")
    
    @staticmethod
    def _create_openai(model: Optional[str], temperature: float, **kwargs):
        """Create OpenAI LLM"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        model = model or "gpt-4"
        
        logger.info(f"Creating OpenAI LLM: {model}")
        
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            **kwargs
        )
    
    @staticmethod
    def _create_ollama(model: Optional[str], temperature: float, **kwargs):
        """Create Ollama LLM (local, free)"""
        model = model or "llama3.2"  # Default to llama3.2 (2B or 3B)
        base_url = kwargs.pop("base_url", "http://localhost:11434")
        
        logger.info(f"Creating Ollama LLM: {model} at {base_url}")
        
        try:
            llm = ChatOllama(
                model=model,
                temperature=temperature,
                base_url=base_url,
                **kwargs
            )
            
            logger.info("Testing Ollama connection...")
            return llm
            
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            logger.info("Make sure Ollama is installed and running:")
            logger.info("  1. Install: https://ollama.ai/download")
            logger.info("  2. Start: ollama serve")
            logger.info(f"  3. Pull model: ollama pull {model}")
            raise
    
    @staticmethod
    def _create_groq(model: Optional[str], temperature: float, **kwargs):
        """Create Groq LLM (cloud, FREE API with fast inference)"""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable not set.\n"
                "Get your FREE API key at: https://console.groq.com/keys"
            )
        
        model = model or "llama-3.3-70b-versatile"  # Default to Llama 3.3 70B (latest)
        
        logger.info(f"Creating Groq LLM: {model}")
        
        return ChatGroq(
            model=model,
            temperature=temperature,
            groq_api_key=api_key,
            **kwargs
        )
    
    @staticmethod
    def _create_openrouter(model: Optional[str], temperature: float, **kwargs):
        """Create OpenRouter LLM (access to 100+ models via one API)"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable not set.\n"
                "Get your API key at: https://openrouter.ai/keys\n"
                "OpenRouter provides access to 100+ models including GPT-4, Claude, Llama, Mixtral, and more!"
            )
        
        # Default to a good free/affordable model
        model = model or "meta-llama/llama-3.1-70b-instruct"
        
        logger.info(f"Creating OpenRouter LLM: {model}")
        
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/yourusername/autonomous-research-agent",
                "X-Title": "Autonomous Research Agent"
            },
            **kwargs
        )
    
    @staticmethod
    def get_recommended_models():
        """Get recommended models for each provider"""
        return {
            "openai": {
                "best": "gpt-4",
                "fast": "gpt-3.5-turbo",
                "affordable": "gpt-3.5-turbo"
            },
            "ollama": {
                "best": "llama3.1:8b",      # 8B parameters, great quality
                "fast": "llama3.2:3b",      # 3B parameters, very fast
                "affordable": "llama3.2:1b", # 1B parameters, ultra-fast, FREE!
                "recommended": [
                    "llama3.2:3b",   # 3B - Fast and capable
                    "llama3.1:8b",   # 8B - Best quality
                    "mistral:7b",    # 7B - Great alternative
                    "phi3:mini",     # 3.8B - Microsoft's efficient model
                    "gemma2:2b",     # 2B - Google's lightweight model
                ]
            },
            "groq": {
                "best": "llama-3.3-70b-versatile",     # 70B - Highest quality, FREE!
                "fast": "llama-3.1-8b-instant",        # 8B - Ultra-fast inference
                "balanced": "mixtral-8x7b-32768",      # Mixtral - Great for long context
                "recommended": [
                    "llama-3.3-70b-versatile",  # 70B - Best quality, FREE
                    "llama-3.1-8b-instant",     # 8B - Fastest, FREE
                    "mixtral-8x7b-32768",       # Mixtral - 32K context
                    "gemma2-9b-it",             # 9B - Google's model
                ]
            },
            "openrouter": {
                "best": "anthropic/claude-3.5-sonnet",           # Claude 3.5 - Best overall
                "affordable": "meta-llama/llama-3.1-70b-instruct", # Llama 3.1 70B - Great value
                "fast": "meta-llama/llama-3.1-8b-instruct",      # Llama 3.1 8B - Fast
                "free": "google/gemma-2-9b-it:free",             # Free tier model
                "recommended": [
                    "meta-llama/llama-3.1-70b-instruct",    # Llama 3.1 70B - Great quality
                    "anthropic/claude-3.5-sonnet",          # Claude - Best reasoning
                    "google/gemini-pro-1.5",                # Gemini Pro - Long context
                    "mistralai/mixtral-8x7b-instruct",      # Mixtral - Good balance
                    "google/gemma-2-9b-it:free",            # Gemma 2 - Free!
                    "meta-llama/llama-3.1-8b-instruct",     # Llama 8B - Fast & cheap
                ]
            }
        }
    
    @staticmethod
    def validate_provider(provider: str) -> bool:
        """Check if provider is available"""
        provider = provider.lower()
        
        if provider == "openai":
            return bool(os.getenv("OPENAI_API_KEY"))
        
        elif provider == "groq":
            return bool(os.getenv("GROQ_API_KEY"))
        
        elif provider == "openrouter":
            return bool(os.getenv("OPENROUTER_API_KEY"))
        
        elif provider == "ollama":
            try:
                import requests
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                return response.status_code == 200
            except:
                return False
        
        return False


def get_default_llm(temperature: float = 0.5, **kwargs):
    """
    Get the default LLM based on available providers
    
    Priority:
    1. Groq (free API, ultra-fast)
    2. Ollama (free, local)
    3. OpenAI (if API key is set)
    
    Args:
        temperature: Generation temperature
        **kwargs: Additional arguments
        
    Returns:
        LLM instance
    """
    if LLMProvider.validate_provider("groq"):
        logger.info("Using Groq (free API, ultra-fast)")
        return LLMProvider.create_llm("groq", temperature=temperature, **kwargs)
    
    if LLMProvider.validate_provider("ollama"):
        logger.info("Using Ollama (local, free)")
        return LLMProvider.create_llm("ollama", temperature=temperature, **kwargs)
    
    if LLMProvider.validate_provider("openai"):
        logger.info("Using OpenAI")
        return LLMProvider.create_llm("openai", temperature=temperature, **kwargs)
    
    raise RuntimeError(
        "No LLM provider available!\n"
        "Option 1 (FREE): Install Ollama\n"
        "  1. Download from https://ollama.ai/download\n"
        "  2. Run: ollama serve\n"
        "  3. Run: ollama pull llama3.2\n"
        "\n"
        "Option 2: Set OpenAI API key\n"
        "  export OPENAI_API_KEY='your-key'\n"
    )


OLLAMA_QUICK_START = """
🚀 OLLAMA QUICK START (100% FREE!)

1. Install Ollama:
   Windows: Download from https://ollama.ai/download
   Linux:   curl -fsSL https://ollama.ai/install.sh | sh
   Mac:     brew install ollama

2. Start Ollama:
   ollama serve

3. Pull a model (choose one):
   ollama pull llama3.2:3b      # Fast, 3B parameters (2GB)
   ollama pull llama3.1:8b      # Best quality, 8B params (4.7GB)
   ollama pull mistral:7b       # Alternative, 7B params (4.1GB)
   ollama pull phi3:mini        # Microsoft, 3.8B params (2.3GB)
   ollama pull gemma2:2b        # Google, 2B params (1.6GB)

4. Run the agent:
   python main.py "your query" --provider ollama --model llama3.2:3b

💡 RECOMMENDED FOR THIS PROJECT:
   - llama3.2:3b  - Perfect balance of speed and quality
   - llama3.1:8b  - Best quality for comprehensive reviews
   - phi3:mini    - Microsoft's efficient model, great for summaries

📊 MODEL COMPARISON:
   Model          Size   Speed    Quality   RAM     Best For
   ────────────────────────────────────────────────────────────
   llama3.2:1b    1B     ⚡⚡⚡⚡   ⭐⭐      4GB    Quick tests
   llama3.2:3b    3B     ⚡⚡⚡     ⭐⭐⭐    8GB    Research agent
   phi3:mini      3.8B   ⚡⚡⚡     ⭐⭐⭐    8GB    Summaries
   mistral:7b     7B     ⚡⚡       ⭐⭐⭐⭐  16GB   Complex analysis
   llama3.1:8b    8B     ⚡⚡       ⭐⭐⭐⭐  16GB   Best quality
"""
