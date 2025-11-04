"""
Main CLI entry point for Autonomous Research Agent
"""
import argparse
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from core.coordinator import ResearchCoordinator
from llm_config import LLMProvider, OLLAMA_QUICK_START


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('research_agent.log')
        ]
    )


def save_results(results: dict, output_dir: str = "output"):
    """
    Save research results to files
    
    Args:
        results: Results dictionary from coordinator
        output_dir: Output directory path
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if results.get("report"):
        report_file = output_path / "literature_review.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(results["report"])
        print(f"\n✓ Literature review saved to: {report_file}")
    
    if results.get("summaries"):
        summaries_file = output_path / "paper_summaries.txt"
        with open(summaries_file, 'w', encoding='utf-8') as f:
            for i, summary in enumerate(results["summaries"], 1):
                f.write(f"\n{'='*60}\n")
                f.write(f"Paper {i}: {summary.get('title', 'Unknown')}\n")
                f.write(f"{'='*60}\n\n")
                f.write(f"Key Findings:\n")
                for finding in summary.get("key_findings", []):
                    f.write(f"- {finding}\n")
                f.write(f"\nMethodology: {summary.get('methodology', 'N/A')}\n")
                f.write(f"\nResults: {summary.get('results', 'N/A')}\n")
                f.write(f"\nRelevance Score: {summary.get('relevance_score', 0)}/10\n")
        print(f"✓ Paper summaries saved to: {summaries_file}")
    
    if results.get("synthesis"):
        synthesis_file = output_path / "synthesis.txt"
        with open(synthesis_file, 'w', encoding='utf-8') as f:
            synthesis = results["synthesis"]
            f.write("RESEARCH SYNTHESIS\n")
            f.write("="*60 + "\n\n")
            f.write(synthesis.get("synthesis_text", ""))
            f.write(f"\n\nTotal Papers Analyzed: {synthesis.get('total_papers', 0)}")
            f.write(f"\nAverage Relevance: {synthesis.get('avg_relevance', 0):.2f}/10")
        print(f"✓ Synthesis saved to: {synthesis_file}")
    
    if results.get("citations"):
        citations_file = output_path / "citations.txt"
        with open(citations_file, 'w', encoding='utf-8') as f:
            f.write("BIBLIOGRAPHY\n")
            f.write("="*60 + "\n\n")
            for citation in results["citations"]:
                f.write(f"{citation}\n\n")
        print(f"✓ Citations saved to: {citations_file}")
    
    print(f"\n✓ All results saved to: {output_path.absolute()}")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Autonomous Literature Review & Research Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "machine learning for healthcare"
  python main.py "quantum computing applications" --max-papers 30 --verbose
  python main.py "climate change models" --citation-style MLA
  python main.py "neural architecture search" --output output/nas_review
  python main.py "transfer learning" --steps search summarize
        """
    )
    
    parser.add_argument(
        "query",
        type=str,
        help="Research query or topic to investigate"
    )
    
    parser.add_argument(
        "--max-papers",
        type=int,
        default=20,
        help="Maximum number of papers to analyze (default: 20)"
    )
    
    parser.add_argument(
        "--citation-style",
        type=str,
        choices=["APA", "MLA", "Chicago", "IEEE", "Harvard"],
        default="APA",
        help="Citation style for bibliography (default: APA)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4",
        help="LLM model to use (default: gpt-4)"
    )
    
    parser.add_argument(
        "--provider",
        type=str,
        choices=["groq", "ollama", "openai"],
        default="groq",
        help="LLM provider (default: groq - FREE API with ultra-fast inference!)"
    )
    
    parser.add_argument(
        "--groq-model",
        type=str,
        help="Groq model (e.g., llama-3.1-70b-versatile, llama-3.1-8b-instant)"
    )
    
    parser.add_argument(
        "--ollama-model",
        type=str,
        help="Ollama model (e.g., llama3.2:3b, llama3.1:8b, mistral:7b)"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.5,
        help="LLM temperature (default: 0.5)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Output directory for results (default: output)"
    )
    
    parser.add_argument(
        "--steps",
        type=str,
        nargs="+",
        choices=["search", "summarize", "synthesize", "cite", "write"],
        help="Specific workflow steps to execute (default: all)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to files"
    )
    
    parser.add_argument(
        "--use-vector-store",
        action="store_true",
        help="Enable vector database for semantic search (requires chromadb)"
    )
    
    parser.add_argument(
        "--fulltext",
        action="store_true",
        help="Enable full-text PDF analysis (downloads and analyzes complete papers)"
    )
    
    parser.add_argument('--dedup-threshold', type=float, default=0.15,
                   help='Semantic deduplication threshold (0.05-0.30, default: 0.15)')
    
    parser.add_argument(
        "--sources",
        type=str,
        nargs="+",
        choices=["arxiv", "semantic_scholar"],
        default=["arxiv", "semantic_scholar"],
        help="Paper sources to search (default: arxiv semantic_scholar)"
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    if args.provider == "groq":
        if not LLMProvider.validate_provider("groq"):
            print("\n" + "="*60)
            print("⚠️  Groq API Key not found!")
            print("="*60)
            print("\n🚀 Get your FREE Groq API key:")
            print("   1. Visit: https://console.groq.com/keys")
            print("   2. Sign up (free)")
            print("   3. Create API key")
            print("   4. Set environment variable:")
            print("      export GROQ_API_KEY='your-api-key'")
            print("      Or add to .env file: GROQ_API_KEY=your-api-key")
            print("\n💡 Groq offers FREE ultra-fast inference with:")
            print("   - Llama 3.1 70B (best quality)")
            print("   - Llama 3.1 8B (fastest)")
            print("   - Mixtral 8x7B (long context)")
            print("="*60 + "\n")
            sys.exit(1)
    elif args.provider == "ollama":
        if not LLMProvider.validate_provider("ollama"):
            print("\n" + "="*60)
            print("⚠️  Ollama not available!")
            print("="*60)
            print(OLLAMA_QUICK_START)
            sys.exit(1)
    elif args.provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            print("\n⚠️  Warning: OPENAI_API_KEY environment variable not set!")
            print("Set it using: export OPENAI_API_KEY='your-api-key'")
            print("Or add it to a .env file\n")
            sys.exit(1)
    
    print("\n" + "="*60)
    print("Autonomous Literature Review & Research Agent")
    print("="*60)
    print(f"\nQuery: {args.query}")
    print(f"Max Papers: {args.max_papers}")
    print(f"Citation Style: {args.citation_style}")
    print(f"Provider: {args.provider.upper()}")
    print(f"Vector Store: {'ENABLED' if args.use_vector_store else 'DISABLED'}")
    print(f"Full-Text Analysis: {'ENABLED' if args.fulltext else 'DISABLED'}")
    
    # Determine model
    if args.provider == "groq":
        model = args.groq_model or "llama-3.1-70b-versatile"
        print(f"Model: {model}")
    elif args.provider == "ollama":
        model = args.ollama_model or "llama3.2:3b"
        print(f"Model: {model}")
    else:
        model = args.model
        print(f"Model: {model}")
    
    print(f"Output: {args.output}")
    print("="*60 + "\n")
    
    if args.use_vector_store:
        try:
            import chromadb
            from langchain_chroma import Chroma
            print("✓ Vector store dependencies available\n")
        except ImportError:
            print("\n⚠️  Vector store dependencies not installed!")
            print("Install with: pip install chromadb langchain-chroma")
            print("And pull embedding model: ollama pull nomic-embed-text\n")
            sys.exit(1)
    
    if args.fulltext:
        try:
            import pypdf2
            import pdfplumber
            import aiohttp
            print("✓ Full-text analysis dependencies available\n")
        except ImportError:
            print("\n⚠️  Full-text analysis dependencies not installed!")
            print("Install with: pip install pypdf2 pdfplumber aiohttp\n")
            sys.exit(1)
    
    try:
        coordinator_model = model if args.provider in ["ollama", "groq"] else args.model
        
        coordinator = ResearchCoordinator(
            provider=args.provider,
            model=coordinator_model,
            temperature=args.temperature,
            citation_style=args.citation_style,
            use_vector_store=args.use_vector_store,
            use_fulltext=args.fulltext,
            sources=args.sources,
            dedup_threshold=args.dedup_threshold
        )
        
        if args.steps:
            print(f"Running custom workflow: {' → '.join(args.steps)}\n")
            results = coordinator.run_custom(
                research_query=args.query,
                max_papers=args.max_papers,
                steps=args.steps,
                verbose=True
            )
        else:
            results = coordinator.run(
                research_query=args.query,
                max_papers=args.max_papers,
                verbose=True
            )
        
        if not results.get("success") or results.get("error"):
            print(f"\n❌ Error: {results.get('error', 'Unknown error')}")
            sys.exit(1)
        
        if not args.no_save:
            save_results(results, args.output)
        
        print("\n" + "="*60)
        print("RESEARCH SUMMARY")
        print("="*60)
        print(f"Papers Found: {len(results.get('papers', []))}")
        print(f"Papers Summarized: {len(results.get('summaries', []))}")
        print(f"Citations Generated: {len(results.get('citations', []))}")
        
        if results.get("synthesis"):
            avg_relevance = results["synthesis"].get("avg_relevance", 0)
            print(f"Average Relevance Score: {avg_relevance:.2f}/10")
        
        if results.get("report"):
            report_length = len(results["report"])
            print(f"Report Length: {report_length:,} characters")
        
        print("="*60)
        print("\n✓ Research complete!\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
