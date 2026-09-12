# Infrastructure Notes

This directory is intended to hold the infrastructure definitions and environment overlays for the project.

## Current design

- `docker-compose.yml` is the primary local infrastructure definition.
- Environment-specific values are passed mainly through container environment variables.
- The architecture separates public ingress from private services.

## Environment profiles

- `docker-compose.yml` is the development profile with local ports and INFO logging.
- `docker-compose.prod.yml` is a production-like overlay with stricter logging and CPU/memory limits.
- Both profiles reuse the same service definitions and receive environment-specific values through `.env`.

The local Compose model is intentionally used instead of Terraform because the assessment requires a reproducible local simulation rather than a real cloud account. The same trust boundaries map to managed cloud networking, compute, database, queue, and monitoring services with minimal conceptual redesign.
