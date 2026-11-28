import pytest

import fsspec
from fsspec.implementations.memory import MemoryFileSystem


def test_failed_upload_does_not_defer_next_write(tmp_path, monkeypatch):
    remote = MemoryFileSystem(global_store=False, skip_instance_cache=True)
    cached = fsspec.filesystem("simplecache", fs=remote, cache_storage=str(tmp_path))
    original_put = remote.put

    def fail_once(*args, **kwargs):
        raise OSError("upload unavailable")

    monkeypatch.setattr(remote, "put", fail_once)
    with pytest.raises(OSError):
        with cached.transaction:
            cached.pipe("/failed", b"old")

    monkeypatch.setattr(remote, "put", original_put)
    cached.pipe("/later", b"new")
    assert remote.cat("/later") == b"new"
