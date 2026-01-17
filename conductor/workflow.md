# Development Workflow - RAG Pro Max

## Branching Strategy
- **Main Branch**: Stable production-ready code.
- **Feature Branches**: `feature/<feature-name>` for new features.
- **Fix Branches**: `fix/<bug-name>` for bug fixes.

## Development Cycle
1. **Branch Out**: `git checkout -b feature/my-feature`
2. **Implementation**: Code following the 4-layer architecture (UI, Service, Common, Utils).
3. **Local Testing**:
    - Run unit tests: `pytest tests/`
    - Run factory tests: `./scripts/test.sh`
    - Target test coverage: **93%+**
4. **Code Quality**:
    - Linting and type checking (if applicable).
    - Ensure no `IndentationError` or `NameError`.
5. **Commit**: Follow the conventional commit format:
    - `<type>(<scope>): <subject>`
    - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`.
6. **PR & Review**: Submit PR with screenshots and test results.

## Testing Standards
- All code must pass the "Factory Test" (`./scripts/test.sh`).
- Critical modules (RAG, Data Analysis, Auth) require comprehensive test coverage.
- Use mock data for integration tests when external services are involved.

## Release Process
- Update `version.json` and `CHANGELOG.md`.
- Run `./scripts/prepare_release.sh`.
- Tag the release in Git.
