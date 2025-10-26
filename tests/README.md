# Tests

Organized test structure for the BrandMind AI project.

## Structure

```
tests/
├── unit/           # Unit tests - test individual functions/classes in isolation
├── integration/    # Integration tests - test component interactions
├── e2e/           # End-to-end tests - test complete workflows
└── README.md      # This file
```

## Test Categories

### Unit Tests (`tests/unit/`)
- Test individual functions, classes, methods in isolation
- Mock external dependencies
- Fast execution
- High coverage of edge cases

### Integration Tests (`tests/integration/`)
- Test interactions between components
- Test with real external services (Crawl4AI, LLMs)
- May require Docker services running
- Examples:
  - `test_crawl4ai_client.py` - Tests Crawl4AI SDK integration
  - `test_unified_scrape_web_content.py` - Tests unified scraping function

### End-to-End Tests (`tests/e2e/`)
- Test complete user workflows
- Test full system integration
- Slowest but most comprehensive

## Running Tests

```bash
# All tests
make test

# Specific directory
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/e2e/ -v

# Specific test file
python tests/integration/test_unified_scrape_web_content.py
```

## Requirements

- Virtual environment activated
- Dependencies installed (`make install-all`)
- For integration tests: Docker services running (Crawl4AI)
- For LLM tests: API keys configured

## Test Output

- Test results saved to `results/` directory
- Timestamped result files for analysis
- Summary reports for each test run