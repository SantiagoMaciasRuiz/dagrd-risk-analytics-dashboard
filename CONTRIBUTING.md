# Contributing

Thanks for your interest in improving this project.

## Quick Start

1. Fork the repository.
2. Create a feature branch:
   - `git checkout -b feat/my-change`
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Run relevant ETL/QA scripts before opening a PR.
5. Open a Pull Request with:
   - What changed
   - Why it changed
   - Validation evidence (logs, screenshots, or output snippets)

## Scope Guidelines

- Keep changes focused and small.
- Do not commit temporary files, virtual environments, or generated extracts.
- Preserve existing file structure under `data/`, `scripts/`, `docs/`, and `powerbi/`.

## Data and Security

- Avoid committing sensitive or private data.
- Use sanitized samples when sharing outputs.

## Suggested Commit Style

- `feat:` new functionality
- `fix:` bug fix
- `docs:` documentation
- `refactor:` internal improvement without behavior change
