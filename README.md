# Orbit Storage

`orbit-storage` defines a provider-neutral asynchronous object storage capability. It has no cloud
SDK, HTTP client, filesystem backend, or dependency on Orbit Core. The separately installable
`orbit-storage-s3`, `orbit-storage-gcs`, and `orbit-storage-azure` packages implement the
`ObjectStore` protocol without making vendor dependencies mandatory for applications that only
need the contract.

```bash
python -m pip install orbit-storage
```

```python
from orbit_storage import ObjectStore


async def archive_report(store: ObjectStore, report: bytes) -> str:
    info = await store.put(
        "reports/weekly.json",
        report,
        content_type="application/json",
        metadata={"team": "analytics"},
    )
    return info.key
```

The protocol provides streaming-capable `put`, `get`, `delete`, paginated `list_page`, and `aclose`.
Uploads accept `bytes` or an async iterable of byte chunks. Downloads return a `StoredObject`; use
it as an async context manager and consume its closeable `ObjectReader` to release the provider
response on normal completion, failure, or cancellation. Concurrent close calls share one cleanup,
and cancellation is propagated only after that cleanup finishes. This avoids requiring whole-object
buffering for large files. Use
`ListObjectsRequest` to validate page size (1–1000), prefix, and bounded opaque continuation tokens.
`put` creates or replaces a key; `get` returns `None` for an absent key; `delete` reports whether
the key existed.
`OBJECT_STORE_DEPENDENCY_KEY` (`orbit.storage`) is the shared Core-container key adapters may use
to expose their implementation consistently.
Object keys are opaque strings bounded to 1,024 UTF-8 bytes—not filesystem paths—and list tokens are
opaque and specific to the provider and configured bucket. The adapter configures its bucket/container, credentials,
transport, retries, and resource lifetime. Conditional writes, versioning, consistency, encryption,
retention, and multipart upload remain provider-specific and are not promised by this contract.

Implementations should raise `StorageConfigurationError` for invalid configuration/arguments and
`StorageOperationError` for sanitized provider failures; do not expose credentials or raw vendor
messages. Cancellation should propagate unchanged. Call `aclose` for resources owned by the store.

## Documentation

The package-specific guides cover [architecture](docs/architecture/overview.md), [operations and security](docs/operations/README.md), and [development](docs/development/README.md), with [security guidance](docs/security/overview.md). The [documentation index](docs/README.md) links to the full package overview and project policies.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
mypy
```

This package is alpha, its API is not stable, and it supports Python 3.11 through 3.14.
Licensed under Apache-2.0.

