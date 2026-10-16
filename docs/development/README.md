# Orbit Storage: development

This repository owns the shared object storage protocol and validated metadata models. Keep
vendor SDK behavior in the provider adapters and review all provider checkouts before changing a
contract used by S3, GCS, or Azure.

## Local setup and checks

From the repository root:

```bash
python -m pip install -e '.[dev]' build
pytest
ruff check src tests
ruff format --check src tests
mypy
python -m build
```

The contract tests run without cloud credentials. They validate input bounds, normalized metadata,
stream ownership, and cancellation-safe `StoredObject` cleanup. They do not validate provider
response behavior, cloud IAM, network access, or multipart transfer handling.

## Changing the contract

Before changing a shared type or method, inspect all provider consumers and consider the effects on
Python type compatibility, wire metadata, upload replay, pagination tokens, and resource cleanup.
Document any new guarantee only if all adapters can honor it; otherwise define a provider-specific
extension. Keep keys opaque and do not add local filesystem assumptions.

Add boundary tests for malformed metadata, Unicode and size limits, token handling, interrupted
streams, and cleanup races when related behavior changes. Update README examples, API docstrings,
architecture, operations, and security docs in the same change. Include migration notes for each
affected adapter.

## OSS contribution expectations

Follow the repository contribution guide, governance, code of conduct, and security policy. Keep
fixtures credential-free, examples explicit about object lifetime, and error messages free of
provider secrets. Report exact local checks and distinguish them from hosted CI or cloud release
validation.
