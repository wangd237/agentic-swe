import fsspec

from fsspec.implementations.zip import ZipFileSystem


def test_cached_archive_published_when_writer_closes(tmp_path):
    writer = ZipFileSystem(
        "simplecache::memory://admission-visible.zip",
        mode="w",
        target_options={"simplecache": {"cache_storage": str(tmp_path / "cache")}},
    )
    writer.pipe_file("note.txt", b"saved")
    writer.close()
    assert fsspec.filesystem("memory").exists("admission-visible.zip")
