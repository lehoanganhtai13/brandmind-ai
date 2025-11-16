# BrandMind AI: AI-powered Mentor for Brand Strategy Development

<p align="center">
  <a href="https://github.com/lehoanganhtai13/brandmind-ai/actions/workflows/ci.yml"><img src="https://github.com/lehoanganhtai13/brandmind-ai/actions/workflows/ci.yml/badge.svg" alt="CI Status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/status-in%20development-blue.svg" alt="Status">
</p>

**BrandMind AI** is an intelligent mentor designed to guide junior marketers through the complex process of brand strategy development, bridging the gap between academic theory and real-world practice.

## 🚀 About The Project

In the marketing world, there's a significant **"Experience Gap"** for junior professionals. They often lack:
*   **Strategic Direction:** Difficulty translating business goals into a coherent brand roadmap.
*   **Expert Guidance:** Limited access to senior mentorship to challenge and refine their ideas.
*   **Resource Constraints:** Inability to afford expensive courses or consultancy.

BrandMind AI is not just another automation tool. It's a **cognitive augmentation system** designed to act as a virtual senior strategist. It doesn't just give you the answers; it teaches you **how to think** by simulating a real-world mentorship process.

## ✨ Key Features

- **Automated Document Parsing**: Ingests and understands PDF documents, extracting key information and summaries.
- **Intelligent Web Crawling**: Crawls websites to gather relevant brand and market data using a dedicated service ([`Crawl4AI`](https://github.com/unclecode/crawl4ai)).
- **Advanced Search**: Utilizes a private, aggregated search engine ([`SearXNG`](https://github.com/searxng/searxng)) to find the most relevant information.
- **AI-Powered Analytics**: Employs Large Language Models (LLMs) for content summarization, analysis, and trend identification.
- **Modular & Extensible**: Built with a clean, service-oriented architecture for easy extension and maintenance.

## 🚀 Getting Started

Follow these steps to get your local development environment up and running.

### 1. Prerequisites

- **Python 3.12**
- **[uv](https://github.com/astral-sh/uv)**: An extremely fast Python package installer and resolver.
- **[Docker](https://www.docker.com/)**: For running the required infrastructure services.

### 2. Clone the Repository

```bash
git clone https://github.com/lehoanganhtai13/brandmind-ai.git
cd brandmind-ai
```

### 3. Start Infrastructure Services

The project relies on external services for crawling and searching. Start them using Docker Compose:

```bash
make services-up
```
*This will start [`SearXNG`](https://github.com/searxng/searxng) and [`Crawl4AI`](https://github.com/unclecode/crawl4ai) in the background. You can check their status with `make services-status`.*

### 4. Install Dependencies

Install all required Python packages for all services using `uv`:

```bash
make install-all
```

You are now ready to start development!

## 🛠️ Development Workflow

We use a `Makefile` to streamline common development tasks.

### Code Quality

Run a full suite of checks, including formatting, linting, type-checking, and security scans. This is the primary command to ensure code quality before committing.

```bash
make typecheck
```

### Formatting

To format the code without running all checks:

```bash
make format
```

### Testing

The test suite currently includes integration tests that require the infrastructure services (see step 3) to be running.

```bash
# Run all tests
make test

# Run tests in watch mode
make test-watch
```

> **Note**: For a full list of available commands and their descriptions, run `make help`.

## 📦 Project Structure

```
brandmind-ai/
├── .github/workflows/   # CI/CD workflows (GitHub Actions)
├── src/
│   ├── shared/          # Shared utilities, models, and clients
│   ├── core/            # Core business logic and processing pipelines
│   ├── config/          # System-wide configuration management
│   ├── prompts/         # LLM prompts organized by feature
│   └── services/        # Service-specific implementations (not used yet)
├── tests/               # Test suites (unit, integration, e2e)
├── infra/               # Infrastructure services (Docker Compose)
├── tasks/               # Detailed task and feature documentation
├── pyproject.toml       # Project metadata and dependencies (PEP 621)
└── Makefile             # Command runner for development tasks
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

When contributing, please follow a rebase workflow rather than a merge workflow for your Pull Requests to maintain a clean commit history.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'feat: Add some AmazingFeature'`)
4.  Rebase your branch onto the target branch (e.g., `main`)
5.  Push to the Branch (`git push --force-with-lease origin feature/AmazingFeature`)
6.  Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
