"""从 fsspec/filesystem_spec#979 提炼出的最小协议前缀实现。"""

from __future__ import annotations


class AbstractFileSystem:
    """只保留 unstrip_protocol 所需的最小接口。"""

    protocol = "abstract"

    def unstrip_protocol(self, path: str) -> str:
        """把内部路径还原为带协议前缀的公开路径。

        这里故意保留真实 issue 的核心缺陷：
        当前实现只要发现路径“以协议名开头”就直接返回原串，
        没有继续检查后面是否真的是 `://` 分隔符。
        """

        if path.startswith(self.protocol):
            return path
        return f"{self.protocol}://{path}"


class S3FileSystem(AbstractFileSystem):
    protocol = "s3"
