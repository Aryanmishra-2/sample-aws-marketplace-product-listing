# Threat Model — AI Agent Marketplace (STRIDE)

## Scope

This threat model covers the AI Agent Marketplace application: frontend, backend agents, and supporting AWS infrastructure.

## STRIDE Analysis

### Spoofing

| Threat | Mitigation |
|--------|-----------|
| Unauthenticated access to the web application | Amazon Cognito User Pool enforces authentication on the ALB. Admin-only user creation. |
| Forged AWS credentials submitted via the UI | Credentials are validated via AWS STS `GetCallerIdentity` before any operations. |

### Tampering

| Threat | Mitigation |
|--------|-----------|
| Modification of S3 knowledge base documents | S3 versioning enabled. Bucket policy restricts write access. Block Public Access enabled. |
| Tampering with agent session state | DynamoDB access scoped to specific tables via IAM policy. Sessions have TTL expiration. |

### Repudiation

| Threat | Mitigation |
|--------|-----------|
| Untracked API calls to AWS services | AWS CloudTrail logging recommended for all regions. CloudWatch log groups created for ECS tasks and agents. |

### Information Disclosure

| Threat | Mitigation |
|--------|-----------|
| Exposure of AWS credentials in source code | No credentials in source. `.env` files gitignored. Environment variables or IAM roles used at runtime. |
| SSRF leaking internal network data | URL validation enforces HTTPS-only, blocks private IP ranges (10.x, 172.16.x, 192.168.x, 169.254.x, 127.x). Redirects disabled. |
| Hardcoded account IDs or PII in public repo | All account IDs replaced with `<YOUR_ACCOUNT_ID>` placeholders. Personal emails removed. |

### Denial of Service

| Threat | Mitigation |
|--------|-----------|
| Resource exhaustion via excessive API calls | Rate limiting recommended (see SECURITY.md). ECS health checks and auto-restart configured. |
| Large payload attacks | Request size limits enforced by ALB and FastAPI defaults. Webpage fetch truncated to 5000 chars. |

### Elevation of Privilege

| Threat | Mitigation |
|--------|-----------|
| Over-permissioned IAM roles | FullAccess managed policies replaced with scoped inline policies listing only required actions. |
| Container escape | Containers run as non-root user (appuser/nextjs). Minimal base images used. |
| Unauthorized AWS Marketplace operations | Marketplace API actions scoped to specific operations (DescribeEntity, StartChangeSet, etc.) rather than wildcards. |

## Residual Risks

- Self-signed TLS certificates are used for internal ALB; production deployments should use ACM-issued certificates with a custom domain.
- Amazon Bedrock Guardrails are recommended but not yet configured for input/output filtering.
- Rate limiting middleware is not yet implemented in the backend.

## Recommendations

1. Enable AWS CloudTrail in all regions for audit logging.
2. Configure Amazon Bedrock Guardrails for prompt injection protection.
3. Implement rate limiting middleware (e.g., slowapi) in the backend.
4. Replace self-signed certificates with ACM-issued certificates for production.
5. Enable AWS Config rules to monitor for IAM policy drift.
