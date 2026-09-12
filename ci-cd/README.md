# CI/CD Pipeline Notes

This folder contains a simplified pipeline simulation for the cloud infrastructure assignment.

## Pipeline stages

1. Validation
2. Testing
3. Security checks
4. Build
5. Deployment
6. Health verification
7. Success or rollback

## Security check behavior

The pipeline scans source, Compose, Dockerfiles, and environment templates for suspicious hard-coded credentials. It also invokes Docker Scout for critical/high fixed image vulnerabilities when Docker is authenticated. Docker Scout exit code `2` blocks the release; an unauthenticated local Docker installation reports a clear prerequisite warning.

The unsafe-release demonstration creates `.env.local` with a bad database secret. The pipeline detects it before build or deployment. Run `scripts/rollback.ps1` afterward to remove the fixture and restore the last healthy local release.

## Important design note

The pipeline intentionally demonstrates the principle that security enforcement must be part of the engineering workflow, not an afterthought.
