# Orbit Storage: security

The object storage contract normalizes metadata and validates several text boundaries, but it does
not decide who may access an object or how stored bytes are protected. Those controls belong to the
application, provider adapter, cloud IAM configuration, and deployment.

## Access control and object keys

Authorize reads, writes, and deletes in the application. The contract has no user or tenant
context and does not enforce key prefixes. If a tenant prefix is part of the access boundary,
derive it from trusted authorization state and validate it server-side; do not accept a caller's
arbitrary prefix as proof of ownership.

Treat keys and continuation tokens as opaque data, not filesystem paths or credentials. Do not
normalize object keys with path functions. The common key validator rejects control characters and
limits UTF-8 size, but does not prevent path-looking segments, public access, or cross-tenant
collisions.

## Upload and download content

Pydantic validation of metadata does not inspect the uploaded file. Treat content type as an
untrusted hint. Apply application-specific size limits, malware scanning, content validation, and
safe download headers where the use case requires them. The protocol accepts streaming sources, so
enforce limits while consuming chunks as well as before upload when a length is known.

Do not log object bytes, sensitive metadata, full keys containing personal information, signed
URLs, credentials, or provider response bodies. Use a separate provider identity with only the
required bucket/container actions. Configure verified TLS for remote endpoints and keep credentials
in approved secret stores.

## Durability and data protection

Encryption at rest, customer-managed keys, versioning, object lock, retention, legal holds, backup,
replication, and deletion behavior are outside the shared contract. Configure and test them in the
provider and account. An ETag is not a portable content hash or integrity assertion. Verify
checksums with an application-supported mechanism when content integrity is critical.

## Vulnerability reporting

Follow the repository [security policy](../../SECURITY.md) for private vulnerability reporting.
This package guidance is not an IAM or cloud security audit.
