"""半自动搜索适合转成 benchmark 的 GitHub issue 候选。"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text


DEFAULT_QUERY = "bug"
DEFAULT_FORMAT = "json"
DEFAULT_LIMIT = 20

FAMILY_QUERY_PRESETS = {
    "并发与协程": [
        "asyncio",
        "async",
        "await",
        "coroutine",
        "\"event loop\"",
        "timeout",
        "cancel",
    ],
    "文件路径与 IO": [
        "pathlib",
        "\"file path\"",
        "\"file url\"",
        "glob",
        "suffix",
        "stem",
        "joinpath",
        "watchfiles",
        "fsspec",
    ],
    "继承、优先级与控制流": [
        "inheritance",
        "override",
        "priority",
        "dispatch",
        "hook",
        "validator",
        "marker",
        "alias",
    ],
}

FAMILY_ALIAS_MAP = {
    "async": "并发与协程",
    "concurrency": "并发与协程",
    "并发": "并发与协程",
    "并发与协程": "并发与协程",
    "path": "文件路径与 IO",
    "io": "文件路径与 IO",
    "路径": "文件路径与 IO",
    "文件路径与 io": "文件路径与 IO",
    "文件路径与 IO": "文件路径与 IO",
    "controlflow": "继承、优先级与控制流",
    "priority": "继承、优先级与控制流",
    "继承": "继承、优先级与控制流",
    "继承、优先级与控制流": "继承、优先级与控制流",
}


def _strip_code_blocks(text: str) -> str:
    return re.sub(r"```.*?```", " ", text, flags=re.DOTALL)


def _strip_urls(text: str) -> str:
    return re.sub(r"https?://\S+", " ", text)


def _normalize_signal_text(*parts: str) -> str:
    combined = " ".join(part for part in parts if part)
    without_code = _strip_code_blocks(combined)
    without_urls = _strip_urls(without_code)
    normalized = re.sub(r"[^a-z0-9_./#+-]+", " ", without_urls.lower())
    return re.sub(r"\s+", " ", normalized).strip()


def _contains_signal(haystack: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, haystack) for pattern in patterns)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(text: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return normalized or "candidate_search"


def normalize_target_family(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    normalized = raw_value.strip()
    if not normalized:
        return None
    return FAMILY_ALIAS_MAP.get(normalized.lower(), normalized)


def build_search_query(*, user_query: str | None, target_family: str | None) -> str:
    base_query = (user_query or DEFAULT_QUERY).strip() or DEFAULT_QUERY
    normalized_target_family = normalize_target_family(target_family)
    if normalized_target_family is None:
        return base_query
    preset_terms = FAMILY_QUERY_PRESETS.get(normalized_target_family)
    if not preset_terms:
        return base_query
    return base_query


def build_search_queries(*, user_query: str | None, target_family: str | None) -> list[str]:
    base_query = (user_query or DEFAULT_QUERY).strip() or DEFAULT_QUERY
    normalized_target_family = normalize_target_family(target_family)
    if normalized_target_family is None:
        return [base_query]
    preset_terms = FAMILY_QUERY_PRESETS.get(normalized_target_family)
    if not preset_terms:
        return [base_query]
    return [base_query, *[f"{base_query} {term}" for term in preset_terms]]


def _next_output_id(output_dir: Path, run_label: str | None = None) -> str:
    existing_numbers: list[int] = []
    prefix = f"candidate_search_{run_label}_" if run_label else "candidate_search_"
    for path in output_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    if run_label:
        return f"{prefix}{next_number:03d}"
    return f"candidate_search_{next_number:03d}"


def _parse_repo_full_name(repository_payload: dict | None, fallback_repo: str) -> str:
    if not repository_payload:
        return fallback_repo
    owner = repository_payload.get("owner", {})
    owner_login = owner.get("login")
    repo_name = repository_payload.get("name")
    if owner_login and repo_name:
        return f"{owner_login}/{repo_name}"
    if repo_name:
        return f"{fallback_repo.split('/')[0]}/{repo_name}"
    return fallback_repo


def _guess_family(title: str, body: str, labels: list[str], repo_full_name: str) -> str:
    haystack = _normalize_signal_text(title, body, " ".join(labels), repo_full_name)
    if _contains_signal(
        haystack,
        [
            r"\basyncio\b",
            r"\btrio\b",
            r"\banyio\b",
            r"\basync\b",
            r"\bawait\b",
            r"\bevent loop\b",
            r"\bcoroutine\b",
            r"\btaskgroup\b",
        ],
    ):
        return "并发与协程"
    if _contains_signal(
        haystack,
        [
            r"\bfilepath\b",
            r"\bfile path\b",
            r"\bfile url\b",
            r"\bwatchfiles\b",
            r"\bfsspec\b",
            r"\bpathlib\b",
            r"\bglob\b",
            r"\bsuffix\b",
            r"\bstem\b",
            r"\bjoinpath\b",
            r"\bmkdir\b",
            r"\brename\b",
        ],
    ):
        return "文件路径与 IO"
    if _contains_signal(
        haystack,
        [
            r"\bvalidator\b",
            r"\binherit(?:ance|ed|s)?\b",
            r"\boverride\b",
            r"\bpriority\b",
            r"\bdispatch\b",
            r"\bhook\b",
            r"\bmarker\b",
            r"\balias\b",
        ],
    ):
        return "继承、优先级与控制流"
    if _contains_signal(
        haystack,
        [
            r"\bparse(?:r|s|d)?\b",
            r"\btoken\b",
            r"\bnormalized?\b",
            r"\bspecifier\b",
            r"\bhostname\b",
            r"\bcharset\b",
            r"\bwrap(?:ping)?\b",
            r"\bline break(?:ing)?\b",
            r"\bunicode\b",
            r"\bunicodeencodeerror\b",
            r"\bunicodedecodeerror\b",
            r"\bencode(?:error|d|r)?\b",
            r"\bdecode(?:error|d|r)?\b",
            r"\bencoding\b",
        ],
    ):
        return "解析与字符串语义"
    if _contains_signal(
        haystack,
        [
            r"\bserializ(?:e|ation)\b",
            r"\btoml\b",
            r"\byaml\b",
            r"\bjson\b",
            r"\brender\b",
            r"\binline table\b",
            r"\bmetadata\b",
            r"\bwheel\b",
        ],
    ):
        return "序列化与反序列化"
    return "其他"


def _extract_target_files(body: str) -> list[str]:
    # 尝试从 issue 正文里抓出看起来像路径的片段，给后续人工筛选一个起点。
    file_pattern = re.compile(
        r"(?:^|[\s`'\"(])(?P<path>(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.(?:py|pyi|txt|md|toml|yaml|yml|json))(?:$|[\s`'\":),])"
    )
    results: list[str] = []
    for match in file_pattern.finditer(body):
        path = match.group("path")
        if path not in results:
            results.append(path)
    return results[:5]


def _guess_test_shape(title: str, body: str) -> str:
    lowered = f"{title}\n{body}".lower()
    if "traceback" in lowered or "error" in lowered or "exception" in lowered:
        return "优先用 2 到 3 个固定输入覆盖：当前报错路径、期望不再报错路径，以及一个相邻回归场景。"
    if "output" in lowered or "expected" in lowered:
        return "优先用 2 到 3 个固定输入输出断言覆盖当前错误行为、期望行为和一个相邻边界场景。"
    return "优先压成 1 到 3 个稳定回归测试，覆盖当前错误行为、期望行为和一个相邻不回归场景。"


def _guess_risk_notes(title: str, body: str, labels: list[str], repo_full_name: str) -> str:
    haystack = _normalize_signal_text(title, body, " ".join(labels), repo_full_name)
    risks: list[str] = []
    if _contains_signal(
        haystack,
        [
            r"\bthread\b",
            r"\brace\b",
            r"\bflaky\b",
            r"\bintermittent\b",
            r"\bnon[- ]deterministic\b",
        ],
    ):
        risks.append("可能涉及并发或时序抖动，需要确认能否压成稳定复现。")
    if _contains_signal(
        haystack,
        [
            r"\bwindows\b",
            r"\blinux\b",
            r"\bmacos\b",
            r"\bplatform[- ]specific\b",
        ],
    ):
        risks.append("可能带平台相关性，需要确认是否能做成跨平台稳定测试。")
    if _contains_signal(
        haystack,
        [
            r"\bnetwork\b",
            r"\bsocket\b",
            r"\bserver\b",
            r"\bdatabase\b",
            r"\bpostgres(?:ql)?\b",
            r"\bmysql\b",
            r"\bredis\b",
        ],
    ):
        risks.append("需要确认是否能去掉外部依赖，避免变成重环境问题。")
    if not risks:
        return "当前看起来边界较清晰，但仍需人工确认是否能压成单模块、少量稳定回归测试。"
    return " ".join(risks)


def _guess_recommendation(*, family: str, title: str, body: str, repo_full_name: str) -> str:
    haystack = _normalize_signal_text(title, body, repo_full_name)
    if family in {"并发与协程", "文件路径与 IO"}:
        if _contains_signal(
            haystack,
            [
                r"\bminimal\b",
                r"\breproduce\b",
                r"\bexpected\b",
                r"\btraceback\b",
                r"\bexample\b",
                r"\boutput\b",
            ],
        ):
            return "high"
        return "medium"
    if family == "解析与字符串语义":
        if _contains_signal(
            haystack,
            [
                r"\bexpected\b",
                r"\bwrap(?:ping)?\b",
                r"\bmissing\b",
                r"\bunicode\b",
                r"\bcharset\b",
                r"\bunicodeencodeerror\b",
                r"\bunicodedecodeerror\b",
                r"\breproduce\b",
                r"\bexample\b",
            ],
        ):
            return "medium"
    if family == "继承、优先级与控制流":
        return "medium"
    return "low"


def _looks_like_github_token(token: str) -> bool:
    normalized = token.strip()
    return normalized.startswith(("ghp_", "gho_", "ghu_", "ghs_", "github_pat_"))


def _run_gh_auth_token(*, extra_env: dict[str, str] | None = None) -> str | None:
    try:
        token_result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=False,
            env=extra_env,
        )
    except FileNotFoundError:
        return None

    if token_result.returncode == 0 and token_result.stdout.strip():
        return token_result.stdout.strip()
    return None


def _resolve_gh_token_candidates(*, explicit_token: str | None = None) -> list[str | None]:
    """按优先级返回可尝试的 gh token 候选。

    这里刻意保留多个候选，而不是只解析单个 token。
    原因是实际运行中经常会出现：

    - 当前 shell 里残留了一个“看起来像 GitHub token”的无效 `GITHUB_TOKEN`
    - 但 `gh` keyring 里其实仍有可用登录态

    如果只返回第一个候选，搜索流程会直接被 401 打断，无法继续回退到 keyring / session。
    """
    candidates: list[str | None] = []
    seen: set[str | None] = set()

    def add_candidate(token: str | None) -> None:
        normalized = token.strip() if isinstance(token, str) else None
        value = normalized or None
        if value in seen:
            return
        seen.add(value)
        candidates.append(value)

    if explicit_token and explicit_token.strip():
        add_candidate(explicit_token)

    for env_name in ("GITHUB_TOKEN", "GH_TOKEN"):
        env_value = os.environ.get(env_name, "").strip()
        if env_value and _looks_like_github_token(env_value):
            add_candidate(env_value)

    # 当环境变量里的 token 失效时，这里仍应优先尝试 keyring 中的 gh 登录态。
    keyring_env = os.environ.copy()
    keyring_env.pop("GITHUB_TOKEN", None)
    keyring_env.pop("GH_TOKEN", None)
    add_candidate(_run_gh_auth_token(extra_env=keyring_env))

    # 最后再尝试当前环境下的 gh auth token，兼容没有环境污染的场景。
    add_candidate(_run_gh_auth_token())

    # 最后保留一个“纯 session fallback”分支，允许直接走 gh 当前会话。
    add_candidate(None)
    return candidates


def _resolve_gh_token(*, explicit_token: str | None = None) -> str | None:
    """解析 gh 认证 token，优先显式传入，其次尝试可用环境变量，最后回退到 keyring。

    Codex 等沙箱子进程往往无法访问 Windows Credential Manager（keyring），
    因此必须在父进程侧提前抓取 token 并通过环境变量注入到 subprocess 中。
    """
    if explicit_token and explicit_token.strip():
        return explicit_token.strip()

    for env_name in ("GITHUB_TOKEN", "GH_TOKEN"):
        env_value = os.environ.get(env_name, "").strip()
        if env_value and _looks_like_github_token(env_value):
            return env_value

    # 当环境变量里的 token 无效时，优先尝试在去掉环境变量污染后从 keyring 抓取。
    keyring_env = os.environ.copy()
    keyring_env.pop("GITHUB_TOKEN", None)
    keyring_env.pop("GH_TOKEN", None)
    keyring_token = _run_gh_auth_token(extra_env=keyring_env)
    if keyring_token:
        return keyring_token

    # 最后再尝试直接读取当前环境下的 gh auth token，兼容没有环境污染的场景。
    raw_token = _run_gh_auth_token()
    if raw_token:
        return raw_token

    return None


def run_gh_search(
    *,
    repo: str,
    queries: list[str],
    state: str,
    labels: list[str],
    limit: int,
    explicit_token: str | None = None,
) -> list[dict]:
    token_candidates = _resolve_gh_token_candidates(explicit_token=explicit_token)
    auth_failure_details: list[str] = []
    last_network_error: str | None = None
    last_other_error: str | None = None

    for token in token_candidates:
        subprocess_env = os.environ.copy()
        if token:
            # 显式注入 token 环境变量，绕开 Windows Credential Manager 访问依赖。
            subprocess_env["GITHUB_TOKEN"] = token
        else:
            # 当 gh 已登录但当前环境无法导出 token 时，仍允许直接走 gh 当前会话。
            # 这样可以把真实阻塞继续暴露到外网访问层，而不是在脚本内提前失败。
            subprocess_env.pop("GITHUB_TOKEN", None)
            subprocess_env.pop("GH_TOKEN", None)

        merged_results: dict[int, dict] = {}
        attempt_failed = False

        for query in queries:
            command = [
                "gh",
                "search",
                "issues",
                query,
                "--repo",
                repo,
                "--state",
                state,
                "--limit",
                str(limit),
                "--json",
                "number,title,url,labels,state,createdAt,body,repository",
            ]
            for label in labels:
                command.extend(["--label", label])

            result = subprocess.run(
                command,
                cwd=REPO_ROOT,
                capture_output=True,
                check=False,
                env=subprocess_env,
            )
            if result.returncode != 0:
                stderr = result.stderr.decode("utf-8", errors="replace").strip()
                stdout = result.stdout.decode("utf-8", errors="replace").strip()
                detail = stderr or stdout or "未知错误"

                if "401" in detail or "Bad credentials" in detail:
                    auth_failure_details.append(detail)
                    attempt_failed = True
                    break
                if "Could not resolve host" in detail or "connection" in detail.lower():
                    last_network_error = detail
                    raise RuntimeError(
                        f"gh 无法连接到 GitHub API（网络或 DNS 问题）。请检查网络连接和代理设置。\n"
                        f"  原始错误: {detail}"
                    )
                last_other_error = detail
                raise RuntimeError(f"gh search issues 失败：{detail}")

            stdout_text = result.stdout.decode("utf-8", errors="replace")
            try:
                payload = json.loads(stdout_text)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"gh search issues 返回了非 JSON 数据：{exc}\n原始输出：{stdout_text[:500]}")
            if not isinstance(payload, list):
                raise RuntimeError(f"gh search issues 返回结果不是列表。原始输出：{stdout_text[:500]}")
            for item in payload:
                issue_number = int(item["number"])
                if issue_number not in merged_results:
                    merged_results[issue_number] = item

        if attempt_failed:
            continue
        return list(merged_results.values())

    if auth_failure_details:
        latest_detail = auth_failure_details[-1]
        raise RuntimeError(
            f"gh 认证失败（401 Bad credentials）。\n"
            f"  已尝试环境变量 token、gh keyring token 与 gh session fallback，但都未成功。\n"
            f"  请运行 `gh auth refresh -h github.com` 或重新登录 `gh auth login`。\n"
            f"  原始错误: {latest_detail}"
        )
    if last_network_error:
        raise RuntimeError(
            f"gh 无法连接到 GitHub API（网络或 DNS 问题）。请检查网络连接和代理设置。\n"
            f"  原始错误: {last_network_error}"
        )
    if last_other_error:
        raise RuntimeError(f"gh search issues 失败：{last_other_error}")
    raise RuntimeError("gh search issues 失败：未拿到任何可用认证路径。")


def build_candidate_summary(raw_issue: dict, fallback_repo: str) -> dict:
    title = str(raw_issue.get("title", "")).strip()
    body = str(raw_issue.get("body", "") or "")
    labels = [str(item.get("name", "")).strip() for item in raw_issue.get("labels", []) if item.get("name")]
    repo_full_name = _parse_repo_full_name(raw_issue.get("repository"), fallback_repo)
    family = _guess_family(title, body, labels, repo_full_name)
    return {
        "repo": repo_full_name,
        "family": family,
        "issue": f"#{raw_issue.get('number')}",
        "issue_number": raw_issue.get("number"),
        "title": title,
        "url": raw_issue.get("url"),
        "labels": labels,
        "state": raw_issue.get("state"),
        "created_at": raw_issue.get("createdAt"),
        "why_it_fits": (
            f"初步命中 `{family}` 方向；标题和正文看起来具备明确错误行为，适合继续人工判题确认。"
        ),
        "expected_target_files": _extract_target_files(body),
        "expected_test_shape": _guess_test_shape(title, body),
        "estimated_difficulty": "medium",
        "risk_notes": _guess_risk_notes(title, body, labels, repo_full_name),
        "recommendation": _guess_recommendation(
            family=family,
            title=title,
            body=body,
            repo_full_name=repo_full_name,
        ),
        "body_excerpt": body[:500],
    }


def sort_candidates(candidates: list[dict]) -> list[dict]:
    recommendation_rank = {"high": 0, "medium": 1, "low": 2}
    family_rank = {
        "并发与协程": 0,
        "文件路径与 IO": 1,
        "继承、优先级与控制流": 2,
        "解析与字符串语义": 3,
        "序列化与反序列化": 4,
        "其他": 5,
    }
    return sorted(
        candidates,
        key=lambda item: (
            recommendation_rank.get(item["recommendation"], 9),
            family_rank.get(item["family"], 9),
            item["issue_number"],
        ),
    )


def build_search_summary(
    *,
    repo: str,
    query: str,
    target_family: str | None,
    state: str,
    labels: list[str],
    limit: int,
    candidates: list[dict],
) -> dict:
    family_counts: dict[str, int] = {}
    recommendation_counts: dict[str, int] = {}
    for candidate in candidates:
        family = candidate["family"]
        recommendation = candidate["recommendation"]
        family_counts[family] = family_counts.get(family, 0) + 1
        recommendation_counts[recommendation] = recommendation_counts.get(recommendation, 0) + 1

    return {
        "created_at": _utc_timestamp(),
        "repo": repo,
        "query": query,
        "target_family": target_family,
        "state": state,
        "labels": labels,
        "limit": limit,
        "candidate_count": len(candidates),
        "family_counts": dict(sorted(family_counts.items())),
        "recommendation_counts": dict(sorted(recommendation_counts.items())),
        "candidates": candidates,
    }


def build_markdown(summary: dict) -> str:
    if not summary["candidates"]:
        return f"""# Candidate Search Results

## Query

- repo: `{summary["repo"]}`
- query: `{summary["query"]}`
- target_family: `{summary.get("target_family") or "(none)"}`
- state: `{summary["state"]}`
- labels: `{", ".join(summary["labels"]) if summary["labels"] else "(none)"}`
- candidate_count: `0`

当前没有找到候选结果。
"""

    candidate_blocks = []
    for index, candidate in enumerate(summary["candidates"], start=1):
        target_files = ", ".join(f"`{path}`" for path in candidate["expected_target_files"]) or "(none guessed)"
        label_text = ", ".join(f"`{label}`" for label in candidate["labels"]) or "(none)"
        candidate_blocks.append(
            f"""{index}. repo: {candidate["repo"]}
   family: {candidate["family"]}
   issue: {candidate["issue"]}
   title: {candidate["title"]}
   url: {candidate["url"]}
   labels: {label_text}
   why_it_fits: {candidate["why_it_fits"]}
   expected_target_files: {target_files}
   expected_test_shape: {candidate["expected_test_shape"]}
   estimated_difficulty: {candidate["estimated_difficulty"]}
   risk_notes: {candidate["risk_notes"]}
   recommendation: {candidate["recommendation"]}"""
        )

    return f"""# Candidate Search Results

## Query

- repo: `{summary["repo"]}`
- query: `{summary["query"]}`
- target_family: `{summary.get("target_family") or "(none)"}`
- state: `{summary["state"]}`
- labels: `{", ".join(summary["labels"]) if summary["labels"] else "(none)"}`
- candidate_count: `{summary["candidate_count"]}`

## Family Counts

{chr(10).join(f"- `{family}`: `{count}`" for family, count in summary["family_counts"].items())}

## Recommendation Counts

{chr(10).join(f"- `{level}`: `{count}`" for level, count in summary["recommendation_counts"].items())}

## Candidates

{chr(10).join(candidate_blocks)}
"""


def resolve_output_path(*, output: str | None, output_dir: Path, run_label: str | None, fmt: str, repo: str) -> Path:
    if output:
        output_path = Path(output)
        if not output_path.is_absolute():
            output_path = (REPO_ROOT / output_path).resolve()
        return output_path

    output_dir.mkdir(parents=True, exist_ok=True)
    auto_label = run_label or _slugify(repo)
    summary_id = _next_output_id(output_dir, auto_label)
    extension = "md" if fmt == "markdown" else "json"
    return output_dir / f"{summary_id}.{extension}"


def parse_labels(raw_values: list[str]) -> list[str]:
    parsed: list[str] = []
    for raw_value in raw_values:
        for label in raw_value.split(","):
            normalized = label.strip()
            if normalized and normalized not in parsed:
                parsed.append(normalized)
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="半自动搜索适合转成 benchmark 的 GitHub issue 候选。")
    parser.add_argument("--repo", required=True, help="目标仓库，例如 python-jsonschema/jsonschema")
    parser.add_argument(
        "--query",
        default=None,
        help="自定义搜索关键词；不传时使用默认 query。",
    )
    parser.add_argument(
        "--target-family",
        default=None,
        help="可选：按缺陷家族启用搜索预设，例如 并发与协程 / 文件路径与 IO / 继承、优先级与控制流。",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="返回候选数量上限。",
    )
    parser.add_argument(
        "--state",
        default="closed",
        choices=["open", "closed"],
        help="issue 状态过滤。",
    )
    parser.add_argument(
        "--labels",
        action="append",
        default=[],
        help="标签过滤，可重复传入，也可传逗号分隔值。",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出文件路径；不传时自动写入 logs/summaries。",
    )
    parser.add_argument(
        "--output-dir",
        default="logs/summaries",
        help="自动生成输出路径时使用的目录。",
    )
    parser.add_argument(
        "--format",
        default=DEFAULT_FORMAT,
        choices=["json", "markdown"],
        help="输出格式。",
    )
    parser.add_argument(
        "--run-label",
        default=None,
        help="自动输出文件名标签。",
    )
    parser.add_argument(
        "--github-token",
        default=None,
        help="GitHub 个人访问 token；不传时依次检查 GITHUB_TOKEN / GH_TOKEN 环境变量和 gh CLI keyring。",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    labels = parse_labels(args.labels)
    target_family = normalize_target_family(args.target_family)
    query = build_search_query(user_query=args.query, target_family=target_family)
    queries = build_search_queries(user_query=args.query, target_family=target_family)
    output_dir = (REPO_ROOT / args.output_dir).resolve()

    raw_issues = run_gh_search(
        repo=args.repo,
        queries=queries,
        state=args.state,
        labels=labels,
        limit=args.limit,
        explicit_token=args.github_token,
    )
    candidates = sort_candidates([build_candidate_summary(item, args.repo) for item in raw_issues])
    summary = build_search_summary(
        repo=args.repo,
        query=query,
        target_family=target_family,
        state=args.state,
        labels=labels,
        limit=args.limit,
        candidates=candidates,
    )

    output_path = resolve_output_path(
        output=args.output,
        output_dir=output_dir,
        run_label=args.run_label,
        fmt=args.format,
        repo=args.repo,
    )
    if args.format == "markdown":
        write_text(output_path, build_markdown(summary))
    else:
        write_json(output_path, summary)

    print(f"candidate_search: repo={args.repo} state={args.state} query={query}")
    print(f"candidate_count: {summary['candidate_count']}")
    print(f"output_path: {output_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
