# Finassistant: An Agentic AI Financial Analyst

[](https://www.google.com/search?q=https://github.com/nishant-ai/finassistant)
[](https://opensource.org/licenses/MIT)

**Finassistant** is an agentic AI analyst designed to synthesize complex financial information from disparate sources (SEC filings, news, market data) into actionable, evidence-backed reports. It moves beyond simple data retrieval to perform multi-step reasoning via a multi-agent workflow, providing users with insights that would typically require hours of manual research.

> **Note:** This project is currently in the initial development phase.

-----

### 🎥 Live Demo & Preview

**[Link to Live Demo - Deployment Pending]**

*(A GIF preview of the final application will be placed here)*

-----

### ✨ Key Features

  * **Multi-Agent Workflow:** Utilizes a sophisticated architecture where an **Orchestrator Agent** delegates tasks to specialized agents (e.g., `SEC_Filing_Analyst`, `Quantitative_Analyst`) for deeper, more accurate analysis.
  * **Advanced Retrieval-Augmented Generation (RAG):** Implements **Hierarchical RAG** to efficiently parse and query dense, lengthy financial documents like SEC 10-K filings.
  * **Domain-Specific Fine-Tuned Model:** Leverages a fine-tuned transformer model for nuanced sentiment analysis on financial news, providing more accurate insights than generic models.
  * **Production-Grade MLOps:** The entire application is containerized with **Docker** and deployed on **Kubernetes (AWS EKS)** using a fully automated **CI/CD pipeline** with GitHub Actions.

-----

### 🏗️ System Architecture

The system is designed as a modern, distributed application deployed on AWS, ensuring scalability and robustness.

-----

### 🛠️ Tech Stack

  * **Backend:** Python, FastAPI, LangGraph
  * **Frontend:** React, TypeScript, Chart.js
  * **Databases:** ChromaDB (Vector Search), Neo4j (Graph RAG - Planned), Redis (Caching)
  * **Deployment:** Docker, Kubernetes (AWS EKS), AWS (S3, ECR), GitHub Actions (CI/CD)

-----

### 🚀 Getting Started

#### Prerequisites

  * Docker and Docker Compose
  * Git

#### Local Development

To run the application locally, clone the repository and use Docker Compose.

```bash
# 1. Clone the repository
git clone https://github.com/nishant-ai/finassistant.git
cd finassistant

# 2. Set up environment variables
# Create a .env file in the backend directory and add the required API keys.
# See backend/.env.example for details.

# 3. Run the application
docker-compose up --build
```

The application will be available at `http://localhost:3000`.


# Finassistant Project Directory Structure

finassistant/
│
├── .github/
│   └── workflows/
│       └── ci-cd-pipeline.yml         # GitHub Actions workflow for testing and deployment
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/                       # FastAPI routers/endpoints (e.g., /analyze)
│   │   │   └── endpoints.py
│   │   ├── agents/                    # LangGraph agent definitions
│   │   │   ├── orchestrator.py
│   │   │   └── specialized_agents.py
│   │   ├── core/                      # App configuration, settings
│   │   │   └── config.py
│   │   ├── models/                    # Pydantic models for API requests/responses
│   │   │   └── schemas.py
│   │   └── tools/                     # Implementations of agent tools
│   │       ├── sec_filing_tool.py
│   │       ├── market_data_tool.py
│   │       └── news_analyzer_tool.py
│   │
│   ├── ml_models/                     # For your fine-tuned model
│   │   └── sentiment_analyzer/
│   │       ├── model.safetensors
│   │       └── config.json
│   │
│   ├── scripts/                       # One-off scripts (e.g., data ingestion)
│   │   └── ingest_sec_filings.py
│   │
│   ├── tests/                         # Unit and integration tests for the backend
│   │   ├── test_agents.py
│   │   └── test_tools.py
│   │
│   ├── .env.example                   # Example environment variables
│   ├── Dockerfile                     # Dockerfile for the backend service
│   └── requirements.txt               # Python dependencies
│
├── frontend/
│   ├── public/                        # Static assets (index.html, favicon)
│   ├── src/
│   │   ├── assets/                    # Images, fonts, etc.
│   │   ├── components/                # Reusable React components (e.g., Chart, AgentStatus)
│   │   ├── hooks/                     # Custom React hooks
│   │   ├── services/                  # API client for communicating with the backend
│   │   ├── styles/                    # CSS or styling files
│   │   └── App.tsx                    # Main React application component
│   │
│   ├── .env.example
│   ├── Dockerfile                     # Dockerfile for the frontend service
│   ├── package.json
│   └── tsconfig.json
│
├── infra/
│   └── k8s/                           # Kubernetes manifest files
│       ├── backend-deployment.yaml
│       ├── frontend-deployment.yaml
│       ├── database-deployment.yaml   # For ChromaDB/Neo4j if self-hosted
│       ├── service.yaml
│       └── ingress.yaml
│
├── .gitignore                         # Standard git ignore file
├── docker-compose.yml                 # For easy local development setup
├── LICENSE                            # Your project's open-source license (e.g., MIT)
└── README.md                          # The high-level project documentation