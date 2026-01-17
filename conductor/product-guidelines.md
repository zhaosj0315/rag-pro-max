# Product Guidelines - RAG Pro Max

## UI/UX Principles
- **4x1 Flat Layout**: All new interfaces must follow a flat, dense layout to maximize information density.
- **Sidebar Centric**: Core tasks and configuration should be triggered or managed via the sidebar.
- **Anti-Mistouch Design**: Ensure critical actions (like deleting a KB) have confirmation steps.
- **Glassmorphism**: Login and high-level UI elements use modern glassmorphism aesthetics.
- **Feedback**: Provide toast notifications for background tasks and state changes.

## Architectural Standards
- **4-Layer Architecture**:
    1. **Presentation Layer**: Streamlit UI (`src/apppro.py`, `src/ui/`).
    2. **Service Layer**: Business logic (`src/services/`, `src/chat/`).
    3. **Common Layer**: Shared components (`src/common/`).
    4. **Utils/Tools Layer**: Low-level helpers (`src/utils/`, `src/file_processor.py`).
- **Zero Redundancy**: Eliminate duplicate code; refactor shared logic into `src/utils/`.
- **Determinism**: Data analysis must be "Build-First" (physical DB ready before use).

## Documentation Standards
- **Sync Requirement**: Documentation MUST be updated alongside code changes (see `docs/standards/DOCUMENTATION_MAINTENANCE_STANDARD.md`).
- **Public Docs**: Maintain `README.md`, `ARCHITECTURE.md`, and `USER_MANUAL.md` as the primary sources of truth.
- **Internal Specs**: Use `CONDUCTOR` for tracking specific development tracks and plans.

## Safety & Security
- **No Secrets**: Never commit API keys or sensitive credentials.
- **Non-Essential Push**: Follow `docs/standards/NON_ESSENTIAL_PUSH_STANDARD.md` to avoid bloating the repository.
- **Sanitization**: All user inputs and file paths must be sanitized.
