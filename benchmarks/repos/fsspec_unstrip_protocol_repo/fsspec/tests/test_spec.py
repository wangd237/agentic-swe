"""fsspec `unstrip_protocol` 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fsspec.spec import AbstractFileSystem, S3FileSystem


class UnstripProtocolTests(unittest.TestCase):
    def test_prefix_lookalike_path_gets_protocol_restored(self) -> None:
        filesystem = AbstractFileSystem()

        result = filesystem.unstrip_protocol("abstract-file")

        self.assertEqual(result, "abstract://abstract-file")

    def test_s3_prefix_lookalike_path_is_not_treated_as_existing_protocol(self) -> None:
        filesystem = S3FileSystem()

        self.assertEqual(filesystem.unstrip_protocol("s3-file"), "s3://s3-file")
        self.assertEqual(filesystem.unstrip_protocol("s3a-file"), "s3://s3a-file")

    def test_existing_protocol_path_is_left_unchanged(self) -> None:
        filesystem = S3FileSystem()

        result = filesystem.unstrip_protocol("s3://bucket/path.txt")

        self.assertEqual(result, "s3://bucket/path.txt")
