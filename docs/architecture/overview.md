# Orbit Storage: architecture and contract

## Package boundaries

`orbit-storage` defines provider-neutral object metadata, upload/download stream contracts,
pagination inputs, and shared errors. It has no cloud SDK, HTTP client, credentials, or Core
dependency. Provider adapters own vendor SDKs, bucket/container configuration, authentication,
transport, retries, and provider-specific failure translation.

```text
application ───── ObjectStore / ObjectInfo ───── orbit-storage
                          ▲
          ┌───────────────┼────────────────┐
          │               │                │
 orbit-storage-s3  orbit-storage-gcs  orbit-storage-azure
   aiobotocore        gcloud-aio        Azure async SDK
```

`OBJECT_STORE_DEPENDENCY_KEY` is `"orbit.storage"`; Core can use it to inject an application-owned
store resource. The adapter that constructs the client owns it through `aclose()`. Do not close one
client independently from both a plugin and a second application shutdown hook.

## Object identity and metadata

Object keys are opaque strings bounded to 1–1,024 UTF-8 bytes. They are not local filesystem paths;
slashes and `..` segments are still key characters and must never be normalized by path utilities.
Control characters are rejected. Providers may impose additional restrictions, which belong in
their adapter documentation.

`ObjectInfo` gives callers a normalized, immutable metadata snapshot: key, byte size, content type,
entity tag, timezone-aware modification time, and bounded string metadata. The model prevents
provider metadata from leaking unvalidated types into the application but is not a signature,
integrity proof, or authorization decision. ETags have provider-defined semantics and are not
universally content hashes.

## Uploads and downloads

`put` accepts in-memory `bytes` or a one-pass async iterable of byte chunks. Streaming avoids
requiring callers to buffer a whole object, but adapters may use bounded internal buffers or
multipart transfer strategies. A consumed stream is not guaranteed to be replayable after a failed
upload; retries and partial-upload cleanup are provider-specific and should be documented.

`get` returns `StoredObject` with metadata and an `ObjectReader`. Callers own the response lifetime:

```python
stored = await store.get("reports/weekly.json")
if stored is not None:
    async with stored:
        async for chunk in stored.body:
            await write_to_destination(chunk)
```

Consume the stream in bounded chunks and close it even on early exit, errors, or cancellation.
Adapters should release the response at EOF and on `aclose()`. Provider errors during stream
consumption must be normalized without returning raw credentials or SDK messages.

## Listing and continuation tokens

`list_page` accepts `ListObjectsRequest` semantics: a prefix, page size from 1 through 1,000, and
an optional opaque continuation token bounded to 4,096 characters. `ObjectPage` contains at most
1,000 normalized metadata entries. Tokens are specific to an adapter and its configured
bucket/container. They are not cursors that applications may decode, authorization credentials,
or portable identifiers across providers. A listing is not a global snapshot; concurrent writes
can affect later pages according to provider behavior.

## Security and provider-specific behavior

The contract rejects control characters in object keys, user metadata, content types, entity tags,
and continuation tokens. It does not authorize callers, encrypt bytes, scan files, validate MIME
content, impose tenant prefixes, or prevent public ACL configuration. Applications and deployments
must provide those controls.

Conditional writes, object versions, retention, legal holds, encryption keys, consistency,
multipart limits, and exact pagination behavior remain provider-specific. Use an adapter-specific
surface where the shared protocol is insufficient; do not infer identical cloud semantics from a
common method signature.

## Source layout and compatibility

- `src/orbit_storage/contracts.py`: validated value models, reader/store protocols, and shared
  exceptions.
- `src/orbit_storage/__init__.py`: documented public imports.

The package is alpha, supports Python `>=3.11,<3.15`, and depends on Pydantic 2.9 or newer
within major version 2. Its public contract can change before a stable release.
