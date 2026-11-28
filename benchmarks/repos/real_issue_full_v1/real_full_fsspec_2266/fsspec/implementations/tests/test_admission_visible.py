import pytest

from fsspec.implementations.memory import MemoryFileSystem


def test_existing_file_is_not_treated_as_directory():
    filesystem = MemoryFileSystem(global_store=False, skip_instance_cache=True)
    filesystem.pipe_file("/reports", b"data")
    with pytest.raises(FileExistsError):
        filesystem.makedirs("/reports", exist_ok=True)
    assert filesystem.cat_file("/reports") == b"data"
