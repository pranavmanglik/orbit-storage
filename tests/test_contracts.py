# Copyright 2026-present Orbit Contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Behavioral checks for bounded object metadata and key validation."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from orbit_storage import (
    ListObjectsRequest,
    ObjectInfo,
    ObjectPage,
    ObjectReader,
    StoredObject,
    validate_object_key,
)


def test_object_key_is_opaque_bounded_text_not_a_path() -> None:
    assert validate_object_key("folder/../object.bin") == "folder/../object.bin"
    assert validate_object_key("🛰" * 256) == "🛰" * 256
    with pytest.raises(ValueError, match="between 1 and 1024"):
        validate_object_key("")
    with pytest.raises(ValueError, match="control characters"):
        validate_object_key("bad\nkey")
    with pytest.raises(ValueError, match="between 1 and 1024"):
        validate_object_key("x" * 1025)
    with pytest.raises(ValueError, match="between 1 and 1024"):
        validate_object_key("🛰" * 257)
    with pytest.raises(ValueError, match="valid UTF-8"):
        validate_object_key("\ud800")


def test_object_info_validates_bounded_metadata_and_is_immutable() -> None:
    info = ObjectInfo(
        key="docs/guide.txt",
        size_bytes=4,
        content_type="text/plain",
        modified_at=datetime.now(UTC),
        metadata={"team": "platform"},
    )
    assert info.metadata == {"team": "platform"}
    assert info.model_dump(mode="json")["metadata"] == {"team": "platform"}
    with pytest.raises(ValidationError):
        info.size_bytes = 5  # type: ignore[misc]
    with pytest.raises(TypeError):
        info.metadata["team"] = "other"
    with pytest.raises(ValidationError, match="must be strings"):
        ObjectInfo(key="x", size_bytes=0, metadata={"attempt": 7})


@pytest.mark.asyncio
async def test_stored_object_stream_closes_on_context_exit() -> None:
    class Reader:
        """Minimal closeable stream for lifecycle tests."""

        def __init__(self) -> None:
            self.chunks = iter((b"one", b"two"))
            self.closed = False

        def __aiter__(self) -> Reader:
            return self

        async def __anext__(self) -> bytes:
            try:
                return next(self.chunks)
            except StopIteration:
                raise StopAsyncIteration from None

        async def aclose(self) -> None:
            self.closed = True

    reader: ObjectReader = Reader()
    stored = StoredObject(info=ObjectInfo(key="x", size_bytes=6), body=reader)
    async with stored as result:
        chunks = [chunk async for chunk in result.body]
        assert chunks == [b"one", b"two"]
    assert isinstance(reader, Reader) and reader.closed
    await stored.aclose()


@pytest.mark.asyncio
async def test_stored_object_concurrent_close_waits_for_one_cleanup_after_cancellation() -> None:
    """Concurrent and cancelled callers cannot interrupt or duplicate response cleanup."""
    entered = asyncio.Event()
    release = asyncio.Event()

    class Reader:
        def __aiter__(self) -> Reader:
            return self

        async def __anext__(self) -> bytes:
            raise StopAsyncIteration

        async def aclose(self) -> None:
            self.close_calls += 1
            entered.set()
            await release.wait()

        def __init__(self) -> None:
            self.close_calls = 0

    reader = Reader()
    stored = StoredObject(info=ObjectInfo(key="x", size_bytes=0), body=reader)
    cancelled = asyncio.create_task(stored.aclose())
    await entered.wait()
    waiter = asyncio.create_task(stored.aclose())
    cancelled.cancel()
    await asyncio.sleep(0)
    assert not cancelled.done()
    assert not waiter.done()

    release.set()
    with pytest.raises(asyncio.CancelledError):
        await cancelled
    await waiter
    assert reader.close_calls == 1


def test_object_page_has_bounded_metadata_entries_and_opaque_token() -> None:
    page = ObjectPage(
        items=(ObjectInfo(key="x", size_bytes=0),),
        continuation_token="vendor-token",
    )
    assert page.items[0].key == "x"
    assert page.continuation_token == "vendor-token"
    with pytest.raises(ValidationError):
        ObjectPage(items=(), continuation_token="x" * 4097)
    with pytest.raises(ValidationError, match="control characters"):
        ObjectPage(items=(), continuation_token="token\r\nheader: value")


def test_list_request_bounds_pages_and_token_inputs() -> None:
    request = ListObjectsRequest(prefix="reports/", limit=25, continuation_token="opaque")
    assert request.limit == 25
    with pytest.raises(ValidationError):
        ListObjectsRequest(limit=1001)
    with pytest.raises(ValidationError):
        ListObjectsRequest(limit=True)
    with pytest.raises(ValidationError):
        ListObjectsRequest(continuation_token="bad\ntoken")
