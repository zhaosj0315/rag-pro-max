# RAG Pro Max REST API Documentation

**Version**: v9.5.37 (aligned with `src/api/fastapi_server.py`)
**Update Date**: 2026-01-26
**Status**: Production Ready

---

## ⚡ Overview

The RAG Pro Max REST API provides programmatic access to knowledge base management and RAG querying capabilities. It runs alongside the main Streamlit application.

**Base URL**: `http://localhost:8502` (Default)

---

## 📋 Core Endpoints

### 1. System Health
```http
GET /health
```
**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T10:00:00",
  "version": "9.5.37"
}
```

### 2. Query Knowledge Base
```http
POST /query
```
**Request**:
```json
{
  "query": "What is the summary of this document?",
  "kb_name": "KB_Test_2026",
  "top_k": 5,
  "use_cache": true
}
```
**Response**:
```json
{
  "answer": "Based on the documents...",
  "sources": [
    { "file_name": "doc.pdf", "score": 0.95, "text": "..." }
  ],
  "metadata": { ... },
  "cached": false
}
```

### 3. List Knowledge Bases
```http
GET /knowledge-bases
```
**Response**:
```json
[
  {
    "name": "KB_Test_2026",
    "document_count": 12,
    "created_at": "2026-01-01",
    "size_mb": 15.5
  }
]
```

---

## 🚀 Advanced Features (v2.0)

### 1. Incremental Update
Updates an existing knowledge base with new or modified files.
```http
POST /incremental-update
```
**Request**:
```json
{
  "kb_name": "KB_Test_2026",
  "file_paths": ["/path/to/new/doc.pdf"],
  "force_update": false
}
```

### 2. Multimodal Upload (File)
Uploads images or mixed documents for OCR processing.
```http
POST /upload-multimodal
```
**Form Data**:
- `kb_name`: (string) Target Knowledge Base
- `file`: (binary) File content

### 3. Multimodal Query
```http
POST /query-multimodal
```
**Request**:
```json
{
  "query": "Describe the chart in the image",
  "kb_name": "KB_Images",
  "include_images": true,
  "include_tables": true
}
```

---

## ⚠️ Limitations & Roadmap

*   **UI-Exclusive Features**: Advanced capabilities introduced in v9.5+ are currently **Streamlit UI exclusive** and NOT yet available via API:
    *   **Omni-Ingestion**: Database snapshots, web crawling, and text pasting.
    *   **Staging Area Management**: `.meta` auditing and staging area cleanup.
    *   **Dual-Core Data Analysis**: Text-to-SQL generation and dashboarding.
    *   **Deep Research**: Expert multi-role synthesis.
*   **Authentication**: The current API server runs in a trusted environment mode (No Auth). Ensure network isolation in production.

---

**Target**: Provide stable, programmatic RAG access for third-party integrations.