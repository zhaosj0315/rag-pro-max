# RAG Pro Max REST API Documentation

**Version**: v9.8.0 (DA-ECP Edition)
**Update Date**: 2026-01-31
**Status**: Production Ready

---

## ⚡ Overview

The RAG Pro Max REST API provides programmatic access to knowledge base management and RAG querying capabilities. It runs alongside the main Streamlit application.

**Base URL**: `http://localhost:8502` (Default)

---

## ⚠️ Limitations & Roadmap

*   **UI-Exclusive Features**: Advanced capabilities introduced in v9.5+ (and v9.8 DA-ECP) are currently **Streamlit UI exclusive** and NOT yet available via API:
    *   **DA-ECP V4.5**: Micro-Profiling, Structure Parsing, and JIT Data Generation.
    *   **Omni-Ingestion**: Database snapshots, web crawling, and text pasting.
    *   **Staging Area Management**: `.meta` auditing and staging area cleanup.
    *   **Deep Research**: Expert multi-role synthesis.
*   **Authentication**: The current API server runs in a trusted environment mode (No Auth). Ensure network isolation in production.

---

**Target**: Provide stable, programmatic RAG access for third-party integrations.