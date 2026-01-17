# Tech Stack - RAG Pro Max

## Core Technologies
- **RAG Framework**: [LlamaIndex](https://www.llamaindex.ai/) - Orchestrates data ingestion, indexing, and retrieval.
- **Vector Database**: [ChromaDB](https://www.trychroma.com/) - Stores and queries document embeddings.
- **Frontend**: [Streamlit](https://streamlit.io/) - Provides the "Command Center UI v7.9".
- **Data Analysis**: 
    - **SQLite**: Physical storage for structured data.
    - **Pandas**: Data manipulation and Schema extraction.
    - **Plotly**: Interactive data visualization.
- **OCR Engine**:
    - **PaddleOCR**: General-purpose OCR.
    - **Apple Vision Framework**: Native OCR for macOS (Darwin).

## Environment & Infrastructure
- **Language**: Python 3.10+
- **Operating Systems**: 
    - Darwin (macOS) - Primary development & optimized environment.
    - Linux - Supported for deployment.
    - Windows - Supported via `start_windows.bat`.
- **Deployment**: Docker & Docker Compose support.

## Dependencies
- `requirements.txt` manages the full list of Python dependencies.
- Native system tools (e.g., `qlmanage` on macOS for previews).
