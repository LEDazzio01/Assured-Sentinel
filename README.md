# Multi-Agent Systems on Azure

Inspired by Dhiba’s *Designing Multi-Agent Systems*, this project demonstrates how to design, coordinate, and deploy intelligent agents in a cloud-native environment. It is both a technical exploration and a portfolio showcase of agent orchestration, lifecycle management, and observability in Azure.

## 📖 Overview
This repository implements a staged build of a multi-agent system:
- Agents: Python classes (including TRAGIC agents) with reasoning, trust, and communication logic
- Coordination: Round-robin and pattern-based orchestration
- Deployment: Containerized agents deployed to Azure Kubernetes Service (AKS) or Azure Container Apps
- Monitoring: Logging and dashboards via Azure Monitor and Application Insights

## ⚙️ Architecture
Agents → Coordination → API → Deployment → Monitoring

- Agents: Encapsulate reasoning and actions
- Coordination: Defines how agents interact and share tasks
- API: FastAPI endpoints for agent actions and health checks
- Deployment: Docker + Azure manifests for scalable hosting
- Monitoring: Observability layer for lifecycle metrics

## 🚀 Quickstart
Clone the repo and install dependencies:
git clone <your-repo-url> cd multi-agent-azure pip install -r requirements.txt

Run the API locally:
python api/server.py

## ☁️ Azure Deployment
1. Build and push container:
docker build -t <acr-name>.azurecr.io/mas:latest . docker push <acr-name>.azurecr.io/mas:latest

2. Deploy to AKS or Azure Container Apps using manifests in `/deployment`
3. Configure Event Grid or Service Bus for agent messaging

## 📊 Monitoring
- Logs agent decisions and coordination events
- Dashboards in Azure Monitor track success/failure rates, latencies, and communication volume

## 🔮 Future Enhancements
- Conformal Prediction: Confidence-aware agent outputs
- Advanced Observability: Drift detection and resilience testing
- World Model Integration: Extend MAS into spatial reasoning environments

## ✨ Why This Project
This project demonstrates:
- Cloud Infrastructure Fluency: Azure-native deployment and monitoring
- Agentic Systems Expertise: Practical application of Dhiba’s MAS framework
- Demonstrates large-scale systems thinking and explainability.
