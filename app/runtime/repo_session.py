"""仓库运行时会话定义。"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RepoSession:
    # 这个结构先固定原始仓库和运行目录概念，后续 phase 再补复制逻辑。
    source_repo_path: Path
    run_workspace_path: Path

    def describe(self) -> dict:
        return {
            "source_repo_path": str(self.source_repo_path),
            "run_workspace_path": str(self.run_workspace_path),
        }
