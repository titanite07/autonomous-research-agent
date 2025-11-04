# Autonomous Literature Review & Research Agent 🔬📚

An intelligent multi-agent system that conducts academic research autonomously using LangGraph and modern AI techniques.

## 🌟 Key Highlights

- ✅ **100% FREE** with Groq or Ollama (no API costs!)
- ✅ **Ultra-Fast** - Up to 800+ tokens/sec with Groq
- ✅ **Multi-Source Search** - arXiv, Semantic Scholar, Springer Nature
- ✅ **AI-Powered Analysis** - LLM-based summarization and synthesis
- ✅ **Professional Output** - Academic-quality literature reviews
- ✅ **Multiple LLM Options** - Groq (cloud), Ollama (local), or OpenAI
- ✅ **5-Minute Setup** - Get your API key and start researching

## 🎯 LLM Options

### Option 1: Groq (Recommended - FREE & FASTEST!)
- **Cost**: FREE ⭐
- **Speed**: Ultra-fast (800+ tokens/sec)
- **Setup**: 5 minutes (just API key)
- **Models**: Llama 3.1 70B, Mixtral 8x7B
- **See**: [GROQ_SETUP.md](GROQ_SETUP.md)

### Option 2: Ollama (FREE & Private)
- **Cost**: FREE
- **Privacy**: 100% local
- **Setup**: 15 minutes (installation)
- **Models**: Llama 3.2, Mistral, Phi-3
- **See**: [OLLAMA_SETUP.md](OLLAMA_SETUP.md)

### Option 3: OpenAI
- **Cost**: ~$0.03/1K tokens
- **Quality**: Excellent
- **Setup**: API key required

## 🌟 Features

- **Search Agent**: Automatically finds relevant academic papers from arXiv, Semantic Scholar, and Springer Nature
- **Semantic Deduplication**: Intelligently removes duplicate/similar papers using vector embeddings (90% similarity threshold)
- **Summarization Agent**: Extracts key findings and insights from research papers
- **Synthesis Agent**: Identifies patterns, trends, and research gaps across multiple papers
- **Citation Agent**: Tracks references and manages bibliographic data (5 styles: APA, MLA, Chicago, IEEE, Harvard)
- **Writing Agent**: Generates comprehensive research summaries and reports

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Research Coordinator                      │
│                     (LangGraph State)                        │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐   ┌──────▼──────┐
│  Search Agent  │   │ Summarization   │   │  Synthesis  │
│   (arXiv +     │──▶│     Agent       │──▶│    Agent    │
│ Semantic Sch.) │   │  (Key Findings) │   │  (Patterns) │
└────────────────┘   └─────────────────┘   └─────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Citation Agent   │
                    │   (References)    │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Writing Agent   │
                    │  (Final Report)   │
                    └───────────────────┘
```

## 🚀 Tech Stack

- **Framework**: LangChain + LangGraph
- **LLM Options**: 
  - **Groq** (FREE API, ultra-fast): Llama 3.1 70B, Mixtral 8x7B
  - **Ollama** (FREE, local): Llama 3.2, Mistral, Phi-3
  - **OpenAI** (paid): GPT-4, GPT-3.5-turbo
- **APIs**: arXiv API, Semantic Scholar API, Springer Nature API
- **Vector Database**: ChromaDB with nomic-embed-text embeddings
- **Semantic Search**: Cosine similarity for duplicate detection and paper matching
- **Backend**: Python 3.11+
- **Data Processing**: scikit-learn, NetworkX, pandas

## 📦 Installation

### Quick Setup (5 Minutes)

**Windows:**
```powershell
.\setup.bat
```

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

### Manual Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/autonomous-research-agent.git
cd autonomous-research-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Get FREE Groq API key:
   - Visit: https://console.groq.com/keys
   - Sign up (free, no credit card)
   - Create API key
   - Set environment variable:
     ```powershell
     # Windows
     $env:GROQ_API_KEY = "gsk_your_key_here"
     
     # Linux/Mac
     export GROQ_API_KEY="gsk_your_key_here"
     ```

## 🎯 Quick Start

### 🚀 One Command to Run Everything!

**Windows (Batch - Easiest!):**
```batch
start.bat
```

**Windows (PowerShell):**
```powershell
.\start.ps1
# OR
.\start-dev.ps1
```

This will automatically:
- ✅ Start the FastAPI backend on `http://localhost:8000`
- ✅ Start the Next.js frontend on `http://localhost:3000`
- ✅ Open both in separate terminal windows
- ✅ Enable auto-reload for both servers

**Access your app:**
- 🌐 **Frontend**: http://localhost:3000
- 🔧 **Backend API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs

**To stop**: Close the terminal windows or press `Ctrl+C` in each

---

### Manual Start (If needed)

**Backend only:**
```bash
# Windows
.venv\Scripts\activate
uvicorn api.main:app --reload --port 8000

# Linux/Mac
source .venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

**Frontend only:**
```bash
cd frontend
npm run dev
```

---

### Using Groq (Recommended - FREE & FAST!)

```bash
# Basic research query with Groq (fast model)
python main.py "quantum computing applications" --provider groq --groq-model llama-3.1-8b-instant

# Quality mode (70B model for better analysis)
python main.py "machine learning healthcare" --provider groq --groq-model llama-3.1-70b-versatile

# Bypass Semantic Scholar rate limits (use arXiv only)
python main.py "climate change AI" --provider groq --groq-model llama-3.1-8b-instant --sources arxiv

# Analyze more papers with custom deduplication threshold
python main.py "deep learning" --provider groq --groq-model llama-3.1-8b-instant --max-papers 20 --sources arxiv --use-vector-store --dedup-threshold 0.20

# Verbose mode to see detailed progress
python main.py "neural networks" --provider groq --groq-model llama-3.1-8b-instant --max-papers 10 --verbose
```

**Groq Model Comparison:**

| Model | Speed | Quality | Use Case | Token Limit |
|-------|-------|---------|----------|-------------|
| `llama-3.1-8b-instant` | ⚡ Ultra-fast (1-4s/call) | Good | Quick research, prototyping | 6,000/request |
| `llama-3.1-70b-versatile` | 🐢 Slower (5-10s/call) | Excellent | Deep analysis, final reports | 6,000/request |

**Performance Benchmarks:**
- **1 paper**: ~38 seconds (8.0/10 relevance)
- **3 papers**: ~14 seconds (8.33/10 relevance)
- **10 papers**: ~84 seconds (8.50/10 relevance)

**Rate Limits:**
- **Requests**: 14,400/hour (automatic retry handling built-in)
- **Tokens**: 6,000/request (automatically managed)

### Using Ollama (Local & Private)

```bash
# First install Ollama: https://ollama.ai/download
ollama serve
ollama pull llama3.2:3b

# Then run with Ollama
python main.py "neural networks" --provider ollama --ollama-model llama3.2:3b
```

### Using OpenAI

```bash
# Set API key
export OPENAI_API_KEY="sk-your-key"

# Run with OpenAI
python main.py "deep learning" --provider openai --model gpt-4
```

### Web Interface

```bash
# Launch Streamlit interface
streamlit run app.py

# Access at http://localhost:8501
```

### Programmatic Usage

```python
from research_agent import ResearchCoordinator

# Initialize coordinator
coordinator = ResearchCoordinator(
    search_sources=["arxiv", "semantic_scholar"],
    max_papers=20,
    model="gpt-4"
)

# Run research pipeline
results = coordinator.research(
    query="neural architecture search optimization",
    depth="comprehensive"  # quick, standard, comprehensive
)

# Access results
print(f"Found {len(results.papers)} relevant papers")
print(f"Key findings: {results.summary}")
print(f"Research gaps: {results.gaps}")
print(f"Generated report: {results.report_path}")
```

## 📊 Features in Detail

### 1. Search Agent
- Multi-source paper discovery (arXiv, Semantic Scholar)
- Intelligent query expansion
- Relevance ranking and filtering
- Duplicate detection
- Citation network exploration

### 2. Summarization Agent
- Abstract and full-text analysis
- Key finding extraction
- Methodology identification
- Results and conclusions summary
- Visual element interpretation

### 3. Synthesis Agent
- Cross-paper pattern recognition
- Trend analysis over time
- Research gap identification
- Contradiction detection
- Emerging themes discovery

### 4. Citation Agent
- Reference extraction and tracking
- Citation network mapping
- Bibliographic data management
- Impact factor analysis
- Citation style formatting (APA, MLA, Chicago)

### 5. Writing Agent
- Literature review generation
- Executive summaries
- Comparative analysis
- Research proposals
- Multiple output formats (Markdown, LaTeX, PDF, HTML)

## 🛠️ Configuration

Edit `config.yaml` to customize agent behavior:

```yaml
search:
  max_papers: 50
  sources: ["arxiv", "semantic_scholar"]
  time_range: "2020-2024"
  
llm:
  provider: "openai"  # openai, anthropic, ollama
  model: "gpt-4"
  temperature: 0.3
  
vector_db:
  type: "chromadb"
  collection_name: "research_papers"
  embedding_model: "text-embedding-ada-002"
  
output:
  format: "markdown"
  include_citations: true
  include_graphs: true
```

## 📚 Paper Sources & API Keys

The system supports multiple academic paper sources for comprehensive research:

### Default Sources (No API Key Required)
- **arXiv** - Open access preprints (physics, CS, math, etc.)
- **Semantic Scholar** - AI-powered academic search engine

### Optional Sources (Requires Free API Keys)

#### Springer Nature
Access thousands of journals from Springer, Nature, BMC, and more.

**Get API Key:**
1. Register at https://dev.springernature.com/signup
2. Get your free API key
3. Add to `.env`:
   ```bash
   SPRINGER_API_KEY=your_springer_key_here
   ```

**Coverage:**
- **3,000+ journals** across all disciplines
- Life sciences, medicine, engineering, physics, chemistry
- Nature journals included (Nature, Nature Medicine, etc.)
- BMC series (BioMed Central)
- High-quality peer-reviewed content

### Usage Example

```bash
# Default: arXiv + Semantic Scholar only
python main.py "machine learning"

# With Springer (if API key configured)
python main.py "machine learning" --sources arxiv semantic_scholar springer

# Springer focus (best for life sciences/medicine)
python main.py "cancer immunotherapy" --sources springer arxiv

# Medical research with comprehensive coverage
python main.py "CRISPR gene editing" --sources springer semantic_scholar
```

**Note:** Papers are automatically deduplicated across sources using DOI and title matching.

## 📁 Project Structure

```
autonomous-research-agent/
├── agents/                      # Individual agent implementations
│   ├── search_agent.py         # Paper search and discovery
│   ├── summarization_agent.py  # Key finding extraction
│   ├── synthesis_agent.py      # Pattern identification
│   ├── citation_agent.py       # Reference management
│   └── writing_agent.py        # Report generation
├── core/                        # Core functionality
│   ├── coordinator.py          # LangGraph orchestration
│   ├── state.py               # Shared state management
│   └── utils.py               # Helper functions
├── integrations/               # External API integrations
│   ├── arxiv_client.py        # arXiv API wrapper
│   ├── semantic_scholar.py    # Semantic Scholar API
│   └── vector_store.py        # Vector database integration
├── web/                        # Web interface
│   ├── app.py                 # Streamlit application
│   └── components/            # UI components
├── tests/                      # Unit and integration tests
├── outputs/                    # Generated reports and data
├── main.py                     # CLI entry point
├── requirements.txt           # Python dependencies
├── config.yaml                # Configuration file
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## ⚙️ CLI Parameters

### Basic Options

```bash
python main.py "your research query" [OPTIONS]
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | **required** | Research topic or question to investigate |
| `--max-papers` | int | 20 | Maximum number of papers to analyze |
| `--output` | str | `output` | Output directory for results |
| `--verbose` | flag | false | Show detailed progress information |

### Provider & Model Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--provider` | str | `groq` | LLM provider: `groq`, `ollama`, or `openai` |
| `--groq-model` | str | `llama-3.1-8b-instant` | Groq model: `llama-3.1-8b-instant` (fast) or `llama-3.1-70b-versatile` (quality) |
| `--ollama-model` | str | `llama3.2:3b` | Ollama model name |
| `--model` | str | `gpt-4` | OpenAI model name |
| `--temperature` | float | 0.5 | LLM temperature (0.0-1.0) |

### Search & Source Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--sources` | list | `arxiv semantic_scholar` | Paper sources: `arxiv`, `semantic_scholar` |
| `--use-vector-store` | flag | false | Enable semantic deduplication with vector database |
| `--dedup-threshold` | float | 0.15 | Semantic similarity threshold (0.05-0.30) |
| `--fulltext` | flag | false | Analyze full paper text (slower, more detailed) |

### Output Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--citation-style` | str | `APA` | Citation format: `APA`, `MLA`, `Chicago`, `IEEE`, `Harvard` |

### **Deduplication Threshold Guide**

The `--dedup-threshold` parameter controls how aggressively similar papers are filtered:

- **0.05-0.10** (Very Strict): Removes papers with even minor similarities
  ```bash
  python main.py "transformers" --dedup-threshold 0.10 --use-vector-store
  ```

- **0.15** (Default): Balanced - removes clear duplicates and near-duplicates
  ```bash
  python main.py "transformers" --use-vector-store
  ```

- **0.20-0.30** (Loose): Only removes very similar papers
  ```bash
  python main.py "transformers" --dedup-threshold 0.25 --use-vector-store
  ```

**When to adjust:**
- **Lower threshold**: Diverse corpus, many unique papers
- **Higher threshold**: Similar papers expected, want broader coverage

### **Example Commands**

```bash
# Fast research with Groq (recommended for quick iterations)
python main.py "neural networks" --provider groq --groq-model llama-3.1-8b-instant --max-papers 10

# High-quality research with Groq (better analysis)
python main.py "quantum computing" --provider groq --groq-model llama-3.1-70b-versatile --max-papers 20

# Avoid Semantic Scholar rate limits (use arXiv only)
python main.py "machine learning" --provider groq --sources arxiv --max-papers 15

# Full-featured research with deduplication
python main.py "deep learning" --provider groq --max-papers 20 --sources arxiv --use-vector-store --dedup-threshold 0.20 --verbose

# Local and private with Ollama
python main.py "AI ethics" --provider ollama --ollama-model llama3.2:3b --max-papers 10
```

## 🔧 Troubleshooting

### Issue: "GROQ_API_KEY not found"

**Solution:**
1. Create a `.env` file in the project root:
   ```bash
   GROQ_API_KEY=gsk_your_key_here
   ```

2. Or set environment variable:
   ```powershell
   # Windows PowerShell
   $env:GROQ_API_KEY = "gsk_your_key_here"
   
   # Linux/Mac
   export GROQ_API_KEY="gsk_your_key_here"
   ```

### Issue: "429 Too Many Requests" (Groq)

**Cause:** Token rate limit exceeded (6,000 tokens/minute)

**Solution:** The system automatically retries. You can also:
- Use `--max-papers` with smaller value
- Switch to `llama-3.1-8b-instant` (uses fewer tokens)
- Wait 60 seconds for token limit reset

### Issue: "429 Too Many Requests" (Semantic Scholar)

**Cause:** API rate limit (100 requests/5 minutes)

**Solution:** Use `--sources arxiv` to bypass Semantic Scholar:
```bash
python main.py "your query" --sources arxiv
```

### Issue: Wrong model error ("model gpt-4 does not exist")

**Cause:** Model parameter mismatch with provider

**Solution:**
- For Groq: Use `--groq-model llama-3.1-8b-instant`
- For Ollama: Use `--ollama-model llama3.2:3b`
- For OpenAI: Use `--model gpt-4`

### Issue: ChromaDB or Vector Store Errors

**Solution:**
1. Install dependencies:
   ```bash
   pip install chromadb ollama-python
   ```

2. Verify Ollama is running (for embeddings):
   ```bash
   ollama serve
   ollama pull nomic-embed-text
   ```

### Issue: Slow performance with 10+ papers

**Optimization tips:**
- Use `--sources arxiv` (faster than Semantic Scholar)
- Use `llama-3.1-8b-instant` instead of 70B model
- Disable `--fulltext` analysis
- Lower `--max-papers` count

### Issue: Poor relevance scores

**Solutions:**
- Enable vector store: `--use-vector-store`
- Use more specific queries
- Increase `--max-papers` for better selection
- Try `llama-3.1-70b-versatile` for better analysis

### Issue: Unicode/Encoding errors in logs

**Cause:** Special characters in paper titles (e.g., ≈, →)

**Solution:** This is a harmless display issue. The functionality works correctly. To suppress:
```bash
python main.py "your query" 2>nul  # Windows
python main.py "your query" 2>/dev/null  # Linux/Mac
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/test_search_agent.py

# With coverage
pytest --cov=agents tests/
```

## 📈 Performance

- **Paper Search**: ~2-5 seconds per query (varies by API)
- **Summarization**: ~5-10 seconds per paper
- **Synthesis**: ~15-30 seconds for 20 papers
- **Full Pipeline**: ~2-5 minutes for comprehensive research (20-50 papers)

## 🎓 Use Cases

1. **Academic Research**: Conduct literature reviews for thesis/dissertations
2. **Grant Writing**: Identify research gaps and prior art
3. **Industry R&D**: Stay updated on latest research trends
4. **Patent Analysis**: Discover prior art and related work
5. **Course Material**: Create reading lists and summaries
6. **Policy Making**: Gather evidence-based research

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## � Documentation

All comprehensive documentation is organized in the `markdowns/` folder:

### 🚀 Getting Started
- **Quick Setup**: [`markdowns/setup/QUICKSTART.md`](markdowns/setup/QUICKSTART.md)
- **Groq Setup**: [`markdowns/setup/GROQ_SETUP.md`](markdowns/setup/GROQ_SETUP.md)
- **Ollama Setup**: [`markdowns/setup/OLLAMA_SETUP.md`](markdowns/setup/OLLAMA_SETUP.md)

### 🤖 AutoGen Framework (NEW!)
- **Quick Start**: [`markdowns/autogen/AUTOGEN_QUICKSTART.md`](markdowns/autogen/AUTOGEN_QUICKSTART.md)
- **Complete Guide**: [`markdowns/autogen/AUTOGEN_GUIDE.md`](markdowns/autogen/AUTOGEN_GUIDE.md)
- **Technical Overview**: [`markdowns/autogen/AUTOGEN_SUMMARY.md`](markdowns/autogen/AUTOGEN_SUMMARY.md)
- **Quick Reference**: [`markdowns/autogen/AUTOGEN_README.md`](markdowns/autogen/AUTOGEN_README.md)

### 📖 Feature Guides
- **Citation Analysis**: [`markdowns/guides/CITATION_ANALYSIS_GUIDE.md`](markdowns/guides/CITATION_ANALYSIS_GUIDE.md)
- **PDF Extraction**: [`markdowns/guides/PDF_EXTRACTION.md`](markdowns/guides/PDF_EXTRACTION.md)
- **Vector Stores**: [`markdowns/guides/VECTOR_STORES.md`](markdowns/guides/VECTOR_STORES.md)
- **Project Structure**: [`markdowns/guides/STRUCTURE.md`](markdowns/guides/STRUCTURE.md)

### 📋 Implementation Reports
- **Project Summary**: [`markdowns/documentation/PROJECT_SUMMARY_REPORT.md`](markdowns/documentation/PROJECT_SUMMARY_REPORT.md)
- **Phase Summaries**: See `markdowns/documentation/PHASE*_*.md`
- **Implementation History**: See `markdowns/documentation/`

### 🗂️ Full Documentation Index
See [`markdowns/README.md`](markdowns/README.md) for complete documentation structure.

## �🙏 Acknowledgments

- [Microsoft AutoGen](https://github.com/microsoft/autogen) - Multi-agent framework
- [LangChain](https://github.com/langchain-ai/langchain) - LLM framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent orchestration
- [arXiv](https://arxiv.org/) - Open access to research papers
- [Semantic Scholar](https://www.semanticscholar.org/) - AI-powered research tool

## 📧 Contact

For questions and support:
- Open an issue on GitHub
- Check documentation in [`markdowns/`](markdowns/) folder
---

**Built with ❤️ by researchers, for researchers**
