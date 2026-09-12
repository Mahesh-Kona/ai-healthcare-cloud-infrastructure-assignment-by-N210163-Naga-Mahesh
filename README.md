# Cloud Infrastructure Simulation for AI Healthcare Platform

Student project submission for a secure, reliable, observable, and scalable cloud infrastructure simulation.

**Author:** Naga Mahesh Kona (`N210163`)  
**Mobile:** 91338899049  
**G-mail:** n210163@rguktn.ac.in  
**Institution:** Rajiv Gandhi University of Knowledge Technologies, Nuzvid  
**Scope:** DevSecOps, cloud engineering, infrastructure, reliability, and operations

This project provides a local, production-style cloud infrastructure simulation for an AI-powered healthcare platform. The goal is to demonstrate secure architecture, automation, observability, deployment safety, and failure recovery without requiring a real cloud account.

## Project goals

- Simulate a secure public/private cloud architecture.
- Provide infrastructure-as-code definitions for reproducible environments.
- Run local services that behave like production workloads.
- Demonstrate health checks, metrics, logging, and alerting.
- Show CI/CD with security validation and rollback behavior.
- Simulate failures such as worker outage, external dependency issues, and failed deployment.

## Core architecture

The solution is composed of the following simulation components:

- Public API service
- Internal AI/agent mock service
- Background worker
- Queue
- Private database
- Mock external EHR system
- Monitoring and alerting stack
- CI/CD pipeline with security gates

## Suggested local stack

- Docker + Docker Compose for local runtime
- Redis for queueing
- PostgreSQL for persistent state
- Python services for API, worker, and AI mock
- Prometheus + Grafana for metrics and dashboards
- GitHub Actions or local scripts for CI/CD simulation

## Repository layout

- `infra/` - infrastructure definitions and environment configuration
- `services/` - application-like services for simulation
- `monitoring/` - Prometheus/Grafana configuration
- `scripts/` - automation helpers for start, stop, load, failure, and recovery
- `docs/` - architecture, security, and incident documentation
- `ci-cd/` - pipeline and validation workflows

## Quick start

1. Review the requirements in `project_requirements_cloud.txt`.
2. Use the sample environment values in `.env.example` if you want explicit local overrides.
3. Launch the local environment with Docker Compose.
4. Run the CI/CD simulation and security checks.
5. Trigger failure scenarios and observe recovery behavior.

### Local startup

```bash
docker compose up --build -d
```

The stack is configured with safe local defaults so it can start even when no `.env` file is present. The API and worker read their database credentials from Compose environment variables, and these default to `healthcare` / `change-me-dev` for local simulation only.

### Production-like local profile

Reuse the same infrastructure with stricter log levels and CPU/memory limits:

```powershell
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

Internal services bind to localhost for local inspection but are not exposed on the network. The API is the controlled public entry point.

### Operations

```powershell
powershell -ExecutionPolicy Bypass -File .\ci-cd\pipeline.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\backup_db.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\restore_db.ps1 -BackupFile .\backups\healthcare-YYYYMMDD-HHMMSS.sql
powershell -ExecutionPolicy Bypass -File .\scripts\rollback.ps1
```

The pipeline performs source validation, secret detection, Compose/build validation, an optional Docker Scout critical/high CVE gate, deployment, and health verification. Run `docker login` first to enable Docker Scout image analysis.

### Key endpoints

- API: http://localhost:18080
- AI mock: http://localhost:19001
- EHR mock: http://localhost:19000
- Prometheus: http://localhost:19090
- Grafana: http://localhost:13000

## Notes

This repository intentionally focuses on infrastructure engineering and operational behavior rather than a full healthcare product implementation.

## Public repository safety

- Never commit `.env`, `.env.local`, database data, generated backups, credentials, or Docker runtime logs.
- Copy `.env.example` to `.env` and provide local values before starting the stack.
- The checked-in Compose files use local simulation defaults only; replace them with a secret manager for real deployments.
- Submission PDFs are stored in `submission/` and can be uploaded directly to the assessment portal.

## Repository validation

```powershell
docker compose config --quiet
docker compose -f docker-compose.yml -f docker-compose.prod.yml config --quiet
python -m compileall services
powershell -ExecutionPolicy Bypass -File .\ci-cd\pipeline.ps1
```

The pipeline validates source files, scans for unsafe configuration, builds the service images, optionally runs Docker Scout image analysis, deploys the environment, and verifies health.
