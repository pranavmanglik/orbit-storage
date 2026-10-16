# Orbit Storage: operations

`orbit-storage` has no runtime cloud settings. Install one of its provider adapters and follow that
package's guidance for endpoint, bucket/container, credentials, TLS, retries, concurrency, and
timeouts. Configuration names and default credential chains are intentionally not shared by this
contract package.

## Lifecycle and dependency injection

The application or plugin that constructs an `ObjectStore` owns its client resources. When using
Orbit Core, register the store under `OBJECT_STORE_DEPENDENCY_KEY` (`"orbit.storage"`) as an
application-managed resource. Otherwise, call and await `store.aclose()` from the creator's
shutdown path. Ensure the same client is not independently closed by multiple lifecycle owners.

Every `StoredObject` returned by `get()` has its own streamed-response lifetime. Use it as an async
context manager, even if the consumer may stop before EOF. Process chunks incrementally to keep
memory bounded. On upload, provide a one-pass async iterator when the full object should not reside
in memory; consult the adapter for chunk sizes, multipart behavior, transfer concurrency, and
cleanup after a failed stream.

## Listing and object metadata

Use bounded pages with a modest `limit` and pass continuation tokens back unchanged to the same
store configuration. Do not decode tokens or reuse them after changing provider, account,
bucket/container, or authorization context. Listings may change between pages while objects are
added or removed.

The common key limit is 1,024 UTF-8 bytes; check provider-specific limits before migration. User
metadata is capped at 128 string entries, with each key/value at most 2,048 characters. Returned
timestamps must include timezone information. `ObjectInfo.etag` is an opaque provider value and
must not be treated as a portable checksum.

## Errors and retries

`StorageConfigurationError` represents invalid caller input or adapter settings.
`StorageOperationError` represents a sanitized provider failure. The API lets cancellation
propagate unchanged. Do not retry a streaming upload by reusing an already-consumed body unless the
source can be rewound and the adapter's multipart cleanup semantics are understood. For object
replacement, versioning, or conditional writes, consult the provider adapter: the shared `put`
contract does not prevent lost updates.

## Production preparation

Validate bucket/container existence and policy, service identity permissions, TLS verification,
client pool and transfer limits, upload abort behavior, downloads interrupted by caller
cancellation, multi-page listings, object versioning and retention, and shutdown with in-flight
transfers in a disposable environment. Contract tests do not validate cloud IAM, network topology,
data durability, backups, or provider failover.
