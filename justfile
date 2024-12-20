default:
    @just --list --unsorted

# ==== codebase ====

# Format codebase
[group('codebase')]
fmt:
    uv run ruff format src

# Lint codebase
[group('codebase')]
lint:
    uv run ruff check src
    uv run ty check src

# Test codebase
[group('codebase')]
test:
    uv run pytest

# ==== script ====

# Process all sites listed in SITES.txt
[group('script')]
all-sites *args:
    uv run python scripts/all-sites.py {{args}}

# List available commands
help:
    @just --list
