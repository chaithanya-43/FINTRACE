# Security guidelines

## Credentials and data

- Never commit credentials or real personal data.
- Read secrets and runtime configuration from environment variables.
- Never store OTPs, UPI PINs, or banking passwords.
- Minimize and classify personal and financial data before implementation.
- Apply least-privilege database credentials and service accounts.

## Evidence integrity

Evidence storage must support:

- secure, access-controlled storage
- SHA-256 integrity hashes
- Ed25519 signatures where appropriate

A SHA-256 hash proves that content matches recorded bytes. It does not prove the evidence existed at a particular time or came from the claimed original source. Preserve chain-of-custody context separately.

## Regulatory decisions

Regulatory outcomes must come from deterministic, versioned, source-backed rules. AI may assist extraction or classification but must not make free-form regulatory decisions.

## Network and application security

- Validate all API input with Pydantic schemas.
- Add authentication and authorization before exposing protected features.
- Use HTTPS and secure secret management in deployed environments.
- Review dependencies and logs for accidental sensitive-data exposure.
