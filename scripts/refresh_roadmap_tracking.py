"""一键刷新 roadmap 持续追踪所需的关键校验与状态产物。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text
from scripts.analyze_benchmark_maturity import analyze_benchmark_maturity
from scripts.audit_semi_real_pipeline import audit_semi_real_pipeline
from scripts.snapshot_roadmap_status import snapshot_roadmap_status
from scripts.validate_tasks import validate_repository


DELTA_FIELD_EXTRACTORS = {
    "headline": lambda summary: summary.get("headline"),
    "validation_passed": lambda summary: summary.get("validation", {}).get("passed"),
    "formal_task_count": lambda summary: summary.get("snapshot_summary", {}).get("current_state", {}).get("formal_task_count"),
    "challenge_task_count": lambda summary: summary.get("snapshot_summary", {}).get("current_state", {}).get("challenge_task_count"),
    "ecosystem_count": lambda summary: summary.get("snapshot_summary", {}).get("current_state", {}).get("ecosystem_count"),
    "candidate_count": lambda summary: summary.get("snapshot_summary", {}).get("current_state", {}).get("candidate_count"),
    "accepted_candidate_count": lambda summary: summary.get("snapshot_summary", {}).get("current_state", {}).get("accepted_candidate_count"),
    "screened_candidate_count": lambda summary: summary.get("snapshot_summary", {}).get("current_state", {}).get("screened_candidate_count"),
    "screened_with_task_count": lambda summary: summary.get("snapshot_summary", {}).get("current_state", {}).get("screened_with_task_count"),
    "imported_candidate_count": lambda summary: summary.get("snapshot_summary", {}).get("current_state", {}).get("imported_candidate_count"),
    "latest_frozen_task_count": lambda summary: summary.get("snapshot_summary", {}).get("current_state", {}).get("latest_frozen_task_count"),
    "frozen_40_streak": lambda summary: summary.get("snapshot_summary", {}).get("current_state", {}).get("frozen_40_streak"),
    "challenge_shortlist_candidate_count": lambda summary: summary.get("snapshot_summary", {}).get("challenge_status", {}).get("shortlist_candidate_count"),
    "challenge_shortlist_screened_with_task_count": lambda summary: summary.get("snapshot_summary", {}).get("challenge_status", {}).get("shortlist_screened_with_task_count"),
    "challenge_accepted_ready_not_in_any_manifest_count": lambda summary: summary.get("snapshot_summary", {}).get("challenge_status", {}).get("accepted_ready_not_in_any_manifest_count"),
    "challenge_next_action": lambda summary: summary.get("snapshot_summary", {}).get("challenge_status", {}).get("next_action"),
    "challenge_auth_env_token_present": lambda summary: summary.get("snapshot_summary", {}).get("challenge_status", {}).get("local_auth_readiness", {}).get("env_token_present"),
    "challenge_auth_env_token_looks_valid": lambda summary: summary.get("snapshot_summary", {}).get("challenge_status", {}).get("local_auth_readiness", {}).get("env_token_looks_valid"),
    "challenge_auth_gh_logged_in": lambda summary: summary.get("snapshot_summary", {}).get("challenge_status", {}).get("local_auth_readiness", {}).get("gh_auth_logged_in"),
    "challenge_auth_token_exportable": lambda summary: summary.get("snapshot_summary", {}).get("challenge_status", {}).get("local_auth_readiness", {}).get("gh_auth_token_exportable"),
    "challenge_auth_preferred_search_mode": lambda summary: summary.get("snapshot_summary", {}).get("challenge_status", {}).get("local_auth_readiness", {}).get("preferred_search_mode"),
    "performance_env_baseline_snapshot_id": lambda summary: summary.get("snapshot_summary", {}).get("performance_status", {}).get("latest_env_baseline_snapshot_id"),
    "performance_env_baseline_mean_of_means_sec": lambda summary: summary.get("snapshot_summary", {}).get("performance_status", {}).get("latest_env_baseline_mean_of_means_sec"),
    "performance_duration_compare_id": lambda summary: summary.get("snapshot_summary", {}).get("performance_status", {}).get("latest_duration_compare_id"),
    "performance_duration_compare_common_average_delta_sec": lambda summary: summary.get("snapshot_summary", {}).get("performance_status", {}).get("latest_duration_compare_common_average_delta_sec"),
    "performance_duration_compare_env_adjusted_common_average_delta_sec": lambda summary: summary.get("snapshot_summary", {}).get("performance_status", {}).get("latest_duration_compare_env_adjusted_common_average_delta_sec"),
}


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _next_refresh_id(summary_dir: Path, run_label: str | None = None) -> str:
    prefix = f"roadmap_tracking_{run_label}_" if run_label else "roadmap_tracking_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def _latest_output_paths(summary_dir: Path, run_label: str | None = None) -> tuple[Path, Path]:
    suffix = f"_{run_label}" if run_label else ""
    return (
        summary_dir / f"roadmap_tracking_latest{suffix}.json",
        summary_dir / f"roadmap_tracking_latest{suffix}.md",
    )


def _history_output_paths(summary_dir: Path, run_label: str | None = None) -> tuple[Path, Path]:
    suffix = f"_{run_label}" if run_label else ""
    return (
        summary_dir / f"roadmap_tracking_history_latest{suffix}.json",
        summary_dir / f"roadmap_tracking_history_latest{suffix}.md",
    )


def _action_board_output_paths(summary_dir: Path, run_label: str | None = None) -> tuple[Path, Path]:
    suffix = f"_{run_label}" if run_label else ""
    return (
        summary_dir / f"roadmap_action_board_latest{suffix}.json",
        summary_dir / f"roadmap_action_board_latest{suffix}.md",
    )


def _status_card_output_paths(summary_dir: Path, run_label: str | None = None) -> tuple[Path, Path]:
    suffix = f"_{run_label}" if run_label else ""
    return (
        summary_dir / f"roadmap_status_card_latest{suffix}.json",
        summary_dir / f"roadmap_status_card_latest{suffix}.md",
    )


def build_tracking_headline(snapshot_summary: dict, *, validation_passed: bool) -> str:
    current_state = snapshot_summary["current_state"]
    validation_status = "OK" if validation_passed else "FAIL"
    return (
        f"roadmap: formal={current_state['formal_task_count']} "
        f"challenge={current_state['challenge_task_count']} "
        f"eco={current_state['ecosystem_count']} "
        f"frozen={current_state['latest_frozen_task_count']} "
        f"streak={current_state['frozen_40_streak']} "
        f"validation={validation_status}"
    )


def _load_previous_summary(summary_path: Path) -> dict | None:
    if not summary_path.exists():
        return None
    return json.loads(summary_path.read_text(encoding="utf-8"))


def build_refresh_delta(previous_summary: dict | None, current_summary: dict) -> tuple[list[str], dict | None]:
    if previous_summary is None:
        return [], None

    field_changes: list[dict[str, object]] = []
    for field_name, extractor in DELTA_FIELD_EXTRACTORS.items():
        previous_value = extractor(previous_summary)
        current_value = extractor(current_summary)
        if previous_value != current_value:
            field_changes.append(
                {
                    "field": field_name,
                    "previous": previous_value,
                    "current": current_value,
                }
            )

    changed_fields = [item["field"] for item in field_changes]
    return changed_fields, {
        "previous_refresh_id": previous_summary.get("refresh_id"),
        "previous_created_at": previous_summary.get("created_at"),
        "change_count": len(field_changes),
        "field_changes": field_changes,
    }


def build_refresh_outcome(previous_summary: dict | None, current_summary: dict, changed_fields: list[str], delta: dict | None) -> dict:
    current_validation_passed = current_summary.get("validation", {}).get("passed", False)
    if not current_validation_passed:
        return {
            "category": "validation_failed",
            "summary": "本次 refresh 未通过仓库级校验，需先处理 validation 错误。",
        }

    if previous_summary is None:
        return {
            "category": "first_refresh",
            "summary": "这是当前标签下首次生成 latest tracking 快照，后续 refresh 将可直接对比变化。",
        }

    if not changed_fields:
        return {
            "category": "no_material_change",
            "summary": "相对上一份 latest，高信号字段没有变化，当前 refresh 主要是在确认状态延续。",
        }

    field_change_map = {
        item["field"]: (item.get("previous"), item.get("current"))
        for item in (delta or {}).get("field_changes", [])
    }
    challenge_task_change = field_change_map.get("challenge_task_count")
    challenge_shortlist_change = field_change_map.get("challenge_shortlist_candidate_count")
    challenge_ready_change = field_change_map.get("challenge_accepted_ready_not_in_any_manifest_count")
    challenge_next_action_change = field_change_map.get("challenge_next_action")
    if (
        challenge_task_change is not None
        and isinstance(challenge_task_change[0], (int, float))
        and isinstance(challenge_task_change[1], (int, float))
        and challenge_task_change[1] > challenge_task_change[0]
        and challenge_ready_change is not None
        and isinstance(challenge_ready_change[0], (int, float))
        and isinstance(challenge_ready_change[1], (int, float))
        and challenge_ready_change[1] < challenge_ready_change[0]
        and (
            challenge_shortlist_change is None
            or (
                isinstance(challenge_shortlist_change[0], (int, float))
                and isinstance(challenge_shortlist_change[1], (int, float))
                and challenge_shortlist_change[1] <= challenge_shortlist_change[0]
            )
        )
    ):
        next_action_summary = ""
        if (
            challenge_next_action_change is not None
            and isinstance(challenge_next_action_change[1], str)
            and challenge_next_action_change[1]
        ):
            next_action_summary = f"；下一步已切换为：{challenge_next_action_change[1]}"
        return {
            "category": "progress",
            "summary": (
                "检测到 challenge manifest 接入推进："
                f"challenge_task_count +{challenge_task_change[1] - challenge_task_change[0]}，"
                f"challenge_accepted_ready_not_in_any_manifest_count {challenge_ready_change[1] - challenge_ready_change[0]}"
                f"{next_action_summary}。"
            ),
        }

    positive_changes: list[str] = []
    negative_changes: list[str] = []
    for item in (delta or {}).get("field_changes", []):
        field_name = item["field"]
        previous_value = item["previous"]
        current_value = item["current"]
        if isinstance(previous_value, (int, float)) and isinstance(current_value, (int, float)):
            change_amount = current_value - previous_value
            if change_amount > 0:
                positive_changes.append(f"{field_name} +{change_amount}")
            elif change_amount < 0:
                negative_changes.append(f"{field_name} {change_amount}")
        elif field_name == "challenge_next_action" and previous_value != current_value:
            if isinstance(previous_value, str) and "重新 sourcing" in previous_value and isinstance(current_value, str):
                positive_changes.append("challenge_next_action updated")
            else:
                positive_changes.append("challenge_next_action changed")
        elif field_name.startswith("challenge_auth_") and previous_value != current_value:
            positive_changes.append(f"{field_name} updated")
        elif field_name == "challenge_shortlist_screened_with_task_count" and isinstance(previous_value, (int, float)) and isinstance(current_value, (int, float)):
            change_amount = current_value - previous_value
            if change_amount > 0:
                positive_changes.append(f"{field_name} +{change_amount}")
            elif change_amount < 0:
                negative_changes.append(f"{field_name} {change_amount}")
        elif field_name.startswith("performance_") and previous_value != current_value:
            positive_changes.append(f"{field_name} updated")
        elif field_name == "accepted_candidate_count" and previous_value is None and isinstance(current_value, (int, float)) and current_value > 0:
            positive_changes.append(f"{field_name} +{current_value}")
        elif field_name == "screened_with_task_count" and previous_value is None and isinstance(current_value, (int, float)) and current_value > 0:
            positive_changes.append(f"{field_name} +{current_value}")
        elif field_name == "validation_passed" and previous_value is False and current_value is True:
            positive_changes.append("validation_passed recovered")
        elif field_name == "validation_passed" and previous_value is True and current_value is False:
            negative_changes.append("validation_passed dropped")

    if positive_changes and not negative_changes:
        return {
            "category": "progress",
            "summary": f"检测到正向推进：{', '.join(positive_changes)}。",
        }

    if negative_changes and not positive_changes:
        return {
            "category": "regression",
            "summary": f"检测到需要关注的回退：{', '.join(negative_changes)}。",
        }

    signal_parts = positive_changes + negative_changes
    if not signal_parts:
        signal_parts = changed_fields
    return {
        "category": "mixed",
        "summary": f"检测到混合变化：{', '.join(signal_parts)}。",
    }


def infer_refresh_outcome_for_history(summary: dict) -> dict:
    existing_outcome = summary.get("refresh_outcome")
    if isinstance(existing_outcome, dict) and existing_outcome.get("category"):
        return existing_outcome

    validation_passed = summary.get("validation", {}).get("passed")
    if validation_passed is False:
        return {
            "category": "validation_failed",
            "summary": "历史 summary 未显式写入 refresh_outcome；根据 validation 结果推断为失败。",
        }

    changed_fields = summary.get("changed_fields", [])
    delta = summary.get("delta")
    previous_latest_summary_json_path = summary.get("previous_latest_summary_json_path")
    if previous_latest_summary_json_path is None:
        return {
            "category": "first_refresh",
            "summary": "历史 summary 未显式写入 refresh_outcome；根据缺少 previous latest 推断为首次 refresh。",
        }

    if not changed_fields and (delta is None or delta.get("change_count", 0) == 0):
        return {
            "category": "no_material_change",
            "summary": "历史 summary 未显式写入 refresh_outcome；根据 delta 为空推断为无实质变化。",
        }

    return {
        "category": "mixed",
        "summary": "历史 summary 未显式写入 refresh_outcome；当前仅按已有 delta 字段回填为 mixed。",
    }


def _build_history_entry(summary: dict, *, summary_json_path: str) -> dict:
    refresh_outcome = infer_refresh_outcome_for_history(summary)
    delta = summary.get("delta") or {}
    return {
        "refresh_id": summary.get("refresh_id"),
        "created_at": summary.get("created_at"),
        "headline": summary.get("headline"),
        "validation_passed": summary.get("validation", {}).get("passed"),
        "outcome_category": refresh_outcome.get("category"),
        "outcome_summary": refresh_outcome.get("summary"),
        "changed_fields": summary.get("changed_fields", []),
        "delta_change_count": delta.get("change_count", 0),
        "progress_track": infer_progress_track(summary),
        "summary_json_path": summary_json_path,
    }


def build_refresh_history(
    *,
    summary_dir: Path,
    run_label: str | None,
    current_summary: dict,
    current_summary_json_path: Path,
    max_recent_entries: int = 10,
) -> dict:
    prefix = f"roadmap_tracking_{run_label}_" if run_label else "roadmap_tracking_"
    history_entries: list[dict] = []
    for path in sorted(summary_dir.glob(f"{prefix}*.json")):
        if path.resolve() == current_summary_json_path.resolve():
            continue
        loaded_summary = _load_previous_summary(path)
        if loaded_summary is None:
            continue
        history_entries.append(_build_history_entry(loaded_summary, summary_json_path=str(path)))

    history_entries.append(_build_history_entry(current_summary, summary_json_path=str(current_summary_json_path)))
    history_entries.sort(key=lambda item: str(item.get("refresh_id")))

    category_counts: dict[str, int] = {}
    no_material_change_streak = 0
    for entry in history_entries:
        category = entry.get("outcome_category") or "unknown"
        category_counts[category] = category_counts.get(category, 0) + 1

    for entry in reversed(history_entries):
        if entry.get("outcome_category") == "no_material_change":
            no_material_change_streak += 1
            continue
        break

    recent_entries = history_entries[-max_recent_entries:]
    return {
        "created_at": _utc_timestamp(),
        "run_label": run_label,
        "latest_refresh_id": current_summary.get("refresh_id"),
        "total_refresh_count": len(history_entries),
        "recent_entry_count": len(recent_entries),
        "category_counts": category_counts,
        "recent_no_material_change_streak": no_material_change_streak,
        "recent_entries": recent_entries,
    }


def build_history_advice(history_summary: dict, current_summary: dict) -> dict:
    recent_entries = history_summary.get("recent_entries", [])
    latest_entry = recent_entries[-1] if recent_entries else {}
    latest_category = latest_entry.get("outcome_category")
    latest_progress_entry = next(
        (entry for entry in reversed(recent_entries) if entry.get("outcome_category") == "progress"),
        None,
    )
    snapshot_summary = current_summary.get("snapshot_summary") or {}
    current_state = snapshot_summary.get("current_state", {})
    challenge_status = snapshot_summary.get("challenge_status", {})
    recent_no_material_change_streak = history_summary.get("recent_no_material_change_streak", 0)
    challenge_task_count = current_state.get("challenge_task_count", 0) or 0
    shortlist_candidate_count = challenge_status.get("shortlist_candidate_count", 0) or 0
    next_action = challenge_status.get("next_action", "")
    has_explicit_challenge_gap = (
        challenge_task_count >= 3
        and shortlist_candidate_count == 0
        and isinstance(next_action, str)
        and "重新 sourcing 第 4 条 challenge 候选" in next_action
    )

    if latest_category == "validation_failed":
        return {
            "category": "fix_validation_first",
            "summary": "最近一次 refresh 卡在 validation，当前应先修复仓库级校验问题，再继续做 roadmap 追踪。",
            "recommended_focus": "governance",
            "recommended_actions": [
                "先处理 validate_tasks 暴露的错误，再重新运行 refresh。",
                "避免基于失败状态继续刷新 maturity 或 snapshot 产物。",
            ],
        }

    if latest_category == "regression":
        return {
            "category": "investigate_regression",
            "summary": "最近一次 refresh 出现了高信号回退，当前应优先回到性能复核或接入治理链路排查原因。",
            "recommended_focus": "performance_track",
            "recommended_actions": [
                "优先检查最近一次 delta 中回退的字段，再决定是否补 stability recheck 或时延定位。",
                "如果回退落在任务规模或 challenge 状态，优先核对 manifest、candidate 和 task 接入状态。",
            ],
        }

    if recent_no_material_change_streak >= 5:
        if has_explicit_challenge_gap:
            return {
                "category": "stalled_tracking",
                "summary": "连续多轮 refresh 没有出现高信号变化，但当前 challenge 第 4 条候选缺口仍然非常明确，适合优先把这条边界展示线继续做实。",
                "recommended_focus": "challenge_track",
                "recommended_actions": [
                    "优先先做 challenge 第 4 条候选 sourcing，并把认证预检、搜索、导入、筛选串成一轮可复用动作。",
                    "如果 live GitHub 检索再次受阻，至少要把阻塞形态、认证状态和下一条可执行命令同步进 latest 文档与 tracking。",
                    "完成 challenge 线实质动作后再 refresh，避免继续只增加 no_material_change streak。",
                ],
                "challenge_next_action": challenge_status.get("next_action"),
            }
        recommended_actions = [
            "暂停只做 refresh 的续跑，切回 A 线继续扩正式真实任务，优先补并发与协程、文件路径与 IO、新生态控制流问题。",
            "如果 challenge 仍未扩到第 2 条，优先继续 sourcing 下一条 challenge 候选。",
            "如果准备推进策略版本，先补新的稳定性或性能诊断证据，而不是仅重复 refresh。",
        ]
        if challenge_task_count >= 2:
            recommended_actions[1] = "challenge 线已不再是最紧急缺口，优先把精力放回正式集扩容或性能证据补强。"
        return {
            "category": "stalled_tracking",
            "summary": "连续多轮 refresh 没有出现高信号变化，说明当前更需要推进主线动作，而不是继续做状态确认。",
            "recommended_focus": "formal_expansion_track",
            "recommended_actions": recommended_actions,
            "challenge_next_action": challenge_status.get("next_action"),
        }

    if latest_category == "progress":
        return {
            "category": "keep_momentum",
            "summary": "最近一次 refresh 已出现正向推进，当前应继续沿同一主线推进，并及时同步文档与评测证据。",
            "recommended_focus": latest_entry.get("progress_track", "active_track"),
            "recommended_actions": [
                "继续沿最近一次产生变化的主线推进，避免在中途改成只做展示层更新。",
                "保持每轮推进后同步 refresh、GUIDE、next_actions 和 optimization_log。",
            ],
        }

    if (
        latest_category == "no_material_change"
        and recent_no_material_change_streak <= 2
        and latest_progress_entry is not None
    ):
        progress_track = latest_progress_entry.get("progress_track", "active_track")
        return {
            "category": "keep_momentum",
            "summary": "最近一轮虽然没有新增高信号变化，但距离上一次 progress 很近，当前更适合继续沿最近证明有效的主线推进。",
            "recommended_focus": progress_track,
            "recommended_actions": [
                "继续沿最近一次产生 progress 的主线推进，避免因为一轮 no_material_change 就切回泛化探索。",
                "补完同主线的新证据或接入动作后再 refresh，确认 progress 是否恢复。",
            ],
            "progress_track": progress_track,
            "source_progress_refresh_id": latest_progress_entry.get("refresh_id"),
        }

    return {
        "category": "monitor_and_continue",
        "summary": "当前 history 没有暴露强回退，但也还没有形成明确推进信号，适合继续按 v2 roadmap 的主线小步推进。",
        "recommended_focus": "performance_or_expansion",
        "recommended_actions": [
            "继续从性能复核常态化、正式集扩容、challenge sourcing 中选择一条最缺口明显的主线推进。",
            "完成一轮实质改动后再 refresh，避免把 tracking 入口当作主工作本身。",
        ],
    }


def infer_progress_track(current_summary: dict) -> str:
    changed_fields = current_summary.get("changed_fields", [])
    challenge_prefixes = ("challenge_",)
    performance_prefixes = ("performance_",)
    formal_fields = {
        "formal_task_count",
        "candidate_count",
        "accepted_candidate_count",
        "ecosystem_count",
        "screened_candidate_count",
        "imported_candidate_count",
    }

    if any(field.startswith(performance_prefixes) for field in changed_fields):
        return "performance_track"
    if any(field.startswith(challenge_prefixes) for field in changed_fields):
        return "challenge_track"
    if any(field in formal_fields for field in changed_fields):
        return "formal_expansion_track"
    if "screened_with_task_count" in changed_fields:
        return "challenge_track"
    return "active_track"


def resolve_priority_track(current_summary: dict, history_advice: dict) -> str:
    progress_track = infer_progress_track(current_summary)
    if progress_track != "active_track":
        return progress_track

    history_track = history_advice.get("progress_track")
    if history_track in {"performance_track", "challenge_track", "formal_expansion_track"}:
        return history_track

    recommended_focus = history_advice.get("recommended_focus")
    if recommended_focus in {"performance_track", "challenge_track", "formal_expansion_track"}:
        return recommended_focus

    return "active_track"


def _build_challenge_search_preflight(local_auth_readiness: dict | None, *, search_command: str) -> tuple[list[str], list[str]]:
    """根据 challenge 本地认证准备度，生成更贴近当前状态的预检动作与命令链。"""
    readiness = local_auth_readiness or {}
    preferred_mode = readiness.get("preferred_search_mode")

    if preferred_mode == "env_token":
        return (
            [
                "当前 latest 检测到环境变量 token 将优先生效；若要排除环境污染，先清理 GITHUB_TOKEN 再复核 gh 会话。",
                "如果 live 检索仍失败，优先把认证或网络阻塞同步进 latest 文档与 tracking，而不是继续空跑 refresh。",
            ],
            [
                "Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue",
                "gh auth status",
                search_command,
            ],
        )

    if preferred_mode == "gh_session_fallback":
        return (
            [
                "当前更可能直接走 gh 已登录会话；若 live 检索仍失败，优先记录 socket 或 API 阻塞，而不是先怀疑 token 导出链路。",
                "如果 live 检索仍失败，优先把认证或网络阻塞同步进 latest 文档与 tracking，而不是继续空跑 refresh。",
            ],
            [
                "gh auth status",
                search_command,
            ],
        )

    if preferred_mode == "gh_auth_token":
        return (
            [
                "当前 gh 会话可导出 token，可优先沿 gh token 路径继续 challenge 搜索。",
                "如果 live 检索仍失败，优先把认证或网络阻塞同步进 latest 文档与 tracking，而不是继续空跑 refresh。",
            ],
            [
                "gh auth status",
                search_command,
            ],
        )

    return (
        [
            "先做 gh 认证预检并清理无效 GITHUB_TOKEN，再继续 challenge 搜索、导入与筛选。",
            "如果 live 检索仍失败，优先把认证或网络阻塞同步进 latest 文档与 tracking，而不是继续空跑 refresh。",
        ],
        [
            "gh auth status",
            "Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue",
            search_command,
        ],
    )


def build_action_board(current_summary: dict, history_summary: dict) -> dict:
    snapshot_summary = current_summary.get("snapshot_summary") or {}
    current_state = snapshot_summary.get("current_state", {})
    challenge_status = snapshot_summary.get("challenge_status", {})
    roadmap_focus = snapshot_summary.get("roadmap_focus", {})
    history_advice = history_summary.get("advice", {})
    refresh_outcome = current_summary.get("refresh_outcome", {})
    challenge_task_count = current_state.get("challenge_task_count") or 0
    next_challenge_slot = challenge_task_count + 1
    progress_track = resolve_priority_track(current_summary, history_advice)
    local_auth_readiness = challenge_status.get("local_auth_readiness", {})
    should_prioritize_challenge_gap = (
        history_advice.get("category") in {"monitor_and_continue", "stalled_tracking"}
        and challenge_task_count >= 3
        and (challenge_status.get("shortlist_candidate_count") or 0) == 0
        and isinstance(challenge_status.get("next_action"), str)
        and "重新 sourcing 第 4 条 challenge 候选" in challenge_status.get("next_action", "")
    )
    concrete_challenge_search_command = (
        "python scripts/search_candidate_issues.py --repo samuelcolvin/watchfiles --query bug --target-family \"文件路径与 IO\" --state closed --labels bug --limit 10 --run-label challenge_a4"
    )
    generic_challenge_search_command = (
        "python scripts/search_candidate_issues.py --query bug --target-family \"文件路径与 IO\" --limit 10 --run-label challenge_a4"
    )

    priorities: list[dict[str, object]]
    if history_advice.get("category") == "fix_validation_first":
        priorities = [
            {
                "priority": 1,
                "track": "governance",
                "reason": "refresh 当前卡在 validation，后续 tracking 结果不应建立在失败状态上。",
                "actions": history_advice.get("recommended_actions", []),
                "commands": [
                    "python scripts/validate_tasks.py",
                    "python scripts/refresh_roadmap_tracking.py --run-label refresh",
                ],
                "docs": [
                    "GUIDE.md",
                    "docs/next_actions.md",
                ],
                "done_signal": "validate_tasks 重新通过，且 refresh 能恢复到 validation=OK。",
                "when_to_refresh": "修复完 validation 错误后立即 refresh，确认 latest 与 history 都恢复正常。",
                "expected_tracking_signals": [
                    "validation.passed 变为 True",
                    "refresh_outcome.category 不再是 validation_failed",
                    "history_advice.category 不再停留在 fix_validation_first",
                ],
            }
        ]
    elif history_advice.get("category") == "stalled_tracking":
        if should_prioritize_challenge_gap:
            preflight_actions, preflight_commands = _build_challenge_search_preflight(
                local_auth_readiness,
                search_command=concrete_challenge_search_command,
            )
            priorities = [
                {
                    "priority": 1,
                    "track": "challenge_track",
                    "reason": "连续多轮没有高信号变化，但 challenge 第 4 条候选缺口仍最具体，且本轮已确认外部动作首先卡在外部访问前置条件。",
                    "actions": [
                        challenge_status.get("next_action", f"继续 sourcing 第 {next_challenge_slot} 条 challenge 候选。"),
                        *preflight_actions,
                    ],
                    "commands": [
                        *preflight_commands,
                        "python scripts/import_search_results.py --search-result logs/summaries/candidate_search_challenge_a4_001.json --recommendation high --limit 3",
                        "python scripts/screen_candidate.py --status imported --limit 3",
                        "python scripts/validate_challenge_shortlist.py",
                        "python scripts/refresh_roadmap_tracking.py --run-label refresh",
                    ],
                    "docs": [
                        "docs/challenge_sourcing_brief_a3.md",
                        "docs/challenge_shortlist.md",
                        "docs/challenge_set.md",
                    ],
                    "done_signal": "challenge shortlist、candidate 或 challenge manifest 至少推进一步，或至少把当前 live sourcing 的真实阻塞状态同步为可复用 handoff 证据。",
                    "when_to_refresh": "完成一轮 challenge 认证预检、搜索、导入、筛选或阻塞记录后 refresh，确认 challenge 线是否重新出现 progress。",
                    "expected_tracking_signals": [
                        "changed_fields 包含 challenge_task_count、challenge_next_action 或 challenge_shortlist_candidate_count",
                        "refresh_outcome.category 不再只是 no_material_change，或 history advice 对 challenge 线的描述发生更新",
                        "action_board 继续把 challenge 线保持在第一优先级，直到 shortlist 或 challenge manifest 发生推进",
                    ],
                },
                {
                    "priority": 2,
                    "track": "formal_expansion_track",
                    "reason": "如果 challenge 线暂时继续受外部环境阻塞，正式集扩容仍是最稳妥的第二主线。",
                    "actions": [
                        "优先补并发与协程、文件路径与 IO、新生态控制流问题。",
                        "将下一轮实质改动落到任务新增或接入治理，而不是继续只跑 refresh。",
                    ],
                    "commands": [
                        "python scripts/search_candidate_issues.py --target-family 并发与协程",
                        "python scripts/search_candidate_issues.py --target-family \"文件路径与 IO\"",
                        "python scripts/import_search_results.py --help",
                    ],
                    "docs": [
                        "docs/v2_roadmap.md",
                        "docs/issue_sourcing_brief_a2.md",
                        "docs/next_actions.md",
                    ],
                    "done_signal": "至少完成一条真实候选的新增、筛选或正式接入，并让正式集相关状态发生可观测变化。",
                    "when_to_refresh": "完成候选导入、task 接入或正式 manifest 更新后 refresh，确认 formal_task_count / candidate 状态是否变化。",
                    "expected_tracking_signals": [
                        "changed_fields 包含 formal_task_count、candidate_count 或 ecosystem_count",
                        "snapshot_summary.current_state.formal_task_count 或 candidate_count 发生变化",
                        "history_advice.category 从 stalled_tracking 开始松动，或 recent_no_material_change_streak 被打断",
                    ],
                },
                {
                    "priority": 3,
                    "track": "performance_track",
                    "reason": "如果准备推进新策略版本，需要先补新的稳定性或性能证据，而不是重复 refresh。",
                    "actions": [
                        "优先补 stability recheck、时延定位或新的 runtime-different compare 证据。",
                    ],
                    "commands": [
                        "python scripts/snapshot_env_baseline.py --repetitions 10 --output-dir logs/env_baselines",
                        "python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_frozen40v68r1_001.json --improved-batch-summary logs/summaries/batch_run_frozen40v69r1_001.json --run-label frozen40_v68_v69",
                        "python scripts/refresh_roadmap_tracking.py --run-label refresh",
                    ],
                    "docs": [
                        "docs/v2_roadmap.md",
                        "docs/next_actions.md",
                        "docs/project_memory.md",
                    ],
                    "done_signal": "新增一份可解释当前性能判断的 stability、时延或环境基线证据产物。",
                    "when_to_refresh": "补完新的性能证据后 refresh，确认 history advice 是否仍要求停留在 stalled_tracking。",
                    "expected_tracking_signals": [
                        "logs/summaries 中新增 env baseline 或 duration compare 产物",
                        "outputs 中出现新的性能相关 summary 路径并被记录到最新 refresh",
                        "history_advice.summary 或 action_board.priority 3 的判断依据发生更新",
                        "如果性能证据足够强，history_advice.category 可能从 stalled_tracking 转向 investigate_regression 或 monitor_and_continue",
                    ],
                },
            ]
        else:
            priorities = [
                {
                    "priority": 1,
                    "track": "formal_expansion_track",
                    "reason": "连续多轮没有高信号变化，最需要新的正式任务推进来打破停滞。",
                    "actions": [
                        "优先补并发与协程、文件路径与 IO、新生态控制流问题。",
                        "将下一轮实质改动落到任务新增或接入治理，而不是继续只跑 refresh。",
                    ],
                    "commands": [
                        "python scripts/search_candidate_issues.py --target-family 并发与协程",
                        "python scripts/search_candidate_issues.py --target-family \"文件路径与 IO\"",
                        "python scripts/import_search_results.py --help",
                    ],
                    "docs": [
                        "docs/v2_roadmap.md",
                        "docs/issue_sourcing_brief_a2.md",
                        "docs/next_actions.md",
                    ],
                    "done_signal": "至少完成一条真实候选的新增、筛选或正式接入，并让正式集相关状态发生可观测变化。",
                    "when_to_refresh": "完成候选导入、task 接入或正式 manifest 更新后 refresh，确认 formal_task_count / candidate 状态是否变化。",
                    "expected_tracking_signals": [
                        "changed_fields 包含 formal_task_count、candidate_count 或 ecosystem_count",
                        "snapshot_summary.current_state.formal_task_count 或 candidate_count 发生变化",
                        "history_advice.category 从 stalled_tracking 开始松动，或 recent_no_material_change_streak 被打断",
                    ],
                },
                {
                    "priority": 2,
                    "track": "challenge_track",
                    "reason": (
                        f"challenge 当前已有 {challenge_task_count} 条，"
                        f"下一步应继续补第 {next_challenge_slot} 条代表系统边界的 hard case。"
                    ),
                    "actions": [
                        challenge_status.get("next_action", f"继续 sourcing 第 {next_challenge_slot} 条 challenge 候选。"),
                    ],
                    "commands": [
                        "python scripts/validate_challenge_shortlist.py",
                        "python scripts/refresh_roadmap_tracking.py --run-label refresh",
                    ],
                    "docs": [
                        "docs/challenge_sourcing_brief_a3.md",
                        "docs/challenge_shortlist.md",
                        "docs/challenge_set.md",
                    ],
                    "done_signal": "challenge shortlist 或 challenge manifest 出现新的有效候选 / 任务，并通过对应校验。",
                    "when_to_refresh": "更新 shortlist、challenge task 或 challenge manifest 后 refresh，确认 challenge_task_count 或 next_action 是否变化。",
                    "expected_tracking_signals": [
                        "changed_fields 包含 challenge_task_count",
                        "snapshot_summary.challenge_status.next_action 发生更新",
                        "snapshot_summary.current_state.challenge_task_count 或 challenge_candidate_count 发生变化",
                    ],
                },
                {
                    "priority": 3,
                    "track": "performance_track",
                    "reason": "如果准备推进新策略版本，需要先补新的稳定性或性能证据，而不是重复 refresh。",
                    "actions": [
                        "优先补 stability recheck、时延定位或新的 runtime-different compare 证据。",
                    ],
                    "commands": [
                        "python scripts/snapshot_env_baseline.py --repetitions 10 --output-dir logs/env_baselines",
                        "python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_frozen40v68r1_001.json --improved-batch-summary logs/summaries/batch_run_frozen40v69r1_001.json --run-label frozen40_v68_v69",
                        "python scripts/refresh_roadmap_tracking.py --run-label refresh",
                    ],
                    "docs": [
                        "docs/v2_roadmap.md",
                        "docs/next_actions.md",
                        "docs/project_memory.md",
                    ],
                    "done_signal": "新增一份可解释当前性能判断的 stability、时延或环境基线证据产物。",
                    "when_to_refresh": "补完新的性能证据后 refresh，确认 history advice 是否仍要求停留在 stalled_tracking。",
                    "expected_tracking_signals": [
                        "logs/summaries 中新增 env baseline 或 duration compare 产物",
                        "outputs 中出现新的性能相关 summary 路径并被记录到最新 refresh",
                        "history_advice.summary 或 action_board.priority 3 的判断依据发生更新",
                        "如果性能证据足够强，history_advice.category 可能从 stalled_tracking 转向 investigate_regression 或 monitor_and_continue",
                    ],
                },
            ]
    elif history_advice.get("category") == "keep_momentum":
        if progress_track == "performance_track":
            priorities = [
                {
                    "priority": 1,
                    "track": "performance_track",
                    "reason": "最近一次 progress 来自性能证据补强，当前应继续沿 performance 线追证，而不是退回泛化续跑。",
                    "actions": [
                        "继续补环境基线、时延对比或 run_tests / pytest startup 下钻证据。",
                        *history_advice.get("recommended_actions", []),
                    ],
                    "commands": [
                        "python scripts/snapshot_env_baseline.py --repetitions 10 --output-dir logs/env_baselines",
                        "python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_frozen40v68r1_001.json --improved-batch-summary logs/summaries/batch_run_frozen40v69r1_001.json --run-label frozen40_v68_v69",
                        "python scripts/refresh_roadmap_tracking.py --run-label refresh",
                    ],
                    "docs": [
                        "docs/v2_roadmap.md",
                        "docs/next_actions.md",
                        "docs/project_memory.md",
                        "docs/optimization_log.md",
                    ],
                    "done_signal": "沿 performance 线继续产出新的环境、时延或阶段诊断证据，并让 changed_fields 保持落在 performance_*。",
                    "when_to_refresh": "每补完一轮新的 performance 证据后 refresh，确认 progress 信号是否延续到同一轨道。",
                    "expected_tracking_signals": [
                        "refresh_outcome.category 维持或再次出现 progress",
                        "changed_fields 继续包含 performance_* 字段",
                    ],
                }
            ]
        elif progress_track == "challenge_track":
            preflight_actions, preflight_commands = _build_challenge_search_preflight(
                local_auth_readiness,
                search_command=generic_challenge_search_command,
            )
            priorities = [
                {
                    "priority": 1,
                    "track": "challenge_track",
                    "reason": "最近一次 progress 来自 challenge 线，当前应继续沿 challenge sourcing / 接入动作推进。",
                    "actions": [
                        challenge_status.get("next_action", f"继续 sourcing 第 {next_challenge_slot} 条 challenge 候选。"),
                        "优先从新生态或当前覆盖较薄生态里找平台 / 环境语境重、但仍能压成稳定本地回归的题。",
                        *preflight_actions,
                        *history_advice.get("recommended_actions", []),
                    ],
                    "commands": [
                        *preflight_commands,
                        "python scripts/import_search_results.py --search-result logs/summaries/candidate_search_challenge_a4_001.json --recommendation high --limit 3",
                        "python scripts/screen_candidate.py --status imported --limit 3",
                        "python scripts/validate_challenge_shortlist.py",
                        "python scripts/refresh_roadmap_tracking.py --run-label refresh",
                    ],
                    "docs": [
                        "docs/challenge_sourcing_brief_a3.md",
                        "docs/challenge_shortlist.md",
                        "docs/optimization_log.md",
                    ],
                    "done_signal": "challenge 线继续产生新的 shortlist / task / manifest 变化，并在 refresh 中保持 challenge_* 字段更新。",
                    "when_to_refresh": "每完成一轮 challenge 动作后 refresh，确认 progress 是否继续落在 challenge 线。",
                    "expected_tracking_signals": [
                        "refresh_outcome.category 维持或再次出现 progress",
                        "changed_fields 继续包含 challenge_* 字段",
                    ],
                }
            ]
        elif progress_track == "formal_expansion_track":
            priorities = [
                {
                    "priority": 1,
                    "track": "formal_expansion_track",
                    "reason": "最近一次 progress 来自正式集扩容，当前应继续沿扩题主线推进，避免中途切散。",
                    "actions": [
                        "继续补并发与协程、文件路径与 IO、新生态控制流问题。",
                        *history_advice.get("recommended_actions", []),
                    ],
                    "commands": [
                        "python scripts/search_candidate_issues.py --target-family 并发与协程",
                        "python scripts/search_candidate_issues.py --target-family \"文件路径与 IO\"",
                        "python scripts/refresh_roadmap_tracking.py --run-label refresh",
                    ],
                    "docs": [
                        "docs/issue_sourcing_brief_a2.md",
                        "docs/v2_roadmap.md",
                        "docs/optimization_log.md",
                    ],
                    "done_signal": "正式集继续出现候选、任务或生态扩容，并在 refresh 中保持 formal / candidate 相关字段变化。",
                    "when_to_refresh": "每完成一轮正式集扩容动作后 refresh，确认 progress 是否继续落在 formal 线。",
                    "expected_tracking_signals": [
                        "refresh_outcome.category 维持或再次出现 progress",
                        "changed_fields 继续包含 formal_task_count / candidate_count / ecosystem_count 等字段",
                    ],
                }
            ]
        else:
            priorities = [
                {
                    "priority": 1,
                    "track": "active_track",
                    "reason": "最近一次 refresh 已有正向推进，应继续沿同一主线推进，避免中途分散。",
                    "actions": history_advice.get("recommended_actions", []),
                    "commands": [
                        "python scripts/refresh_roadmap_tracking.py --run-label refresh",
                    ],
                    "docs": [
                        "GUIDE.md",
                        "docs/optimization_log.md",
                    ],
                    "done_signal": "最近一次推进产生新的高信号字段变化，并完成文档与评测同步。",
                    "when_to_refresh": "每完成一轮同主线推进后 refresh，确认 progress 信号是否延续。",
                    "expected_tracking_signals": [
                        "refresh_outcome.category 维持或再次出现 progress",
                        "changed_fields 保持与当前推进主线一致",
                    ],
                }
            ]
    else:
        if should_prioritize_challenge_gap:
            preflight_actions, preflight_commands = _build_challenge_search_preflight(
                local_auth_readiness,
                search_command=generic_challenge_search_command,
            )
            priorities = [
                {
                    "priority": 1,
                    "track": "challenge_track",
                    "reason": "challenge 线当前缺口最具体：第 4 条候选仍未建立，且 shortlist 为空，适合优先把这条边界展示线继续做实。",
                    "actions": [
                        challenge_status.get("next_action", f"继续 sourcing 第 {next_challenge_slot} 条 challenge 候选。"),
                        "优先从新生态或覆盖较薄生态里找平台 / 环境语境重、但仍可压成稳定本地回归的题。",
                        *preflight_actions,
                    ],
                    "commands": [
                        *preflight_commands,
                        "python scripts/import_search_results.py --search-result logs/summaries/candidate_search_challenge_a4_001.json --recommendation high --limit 3",
                        "python scripts/screen_candidate.py --status imported --limit 3",
                        "python scripts/validate_challenge_shortlist.py",
                        "python scripts/refresh_roadmap_tracking.py --run-label refresh",
                    ],
                    "docs": [
                        "docs/challenge_sourcing_brief_a3.md",
                        "docs/challenge_shortlist.md",
                        "docs/challenge_set.md",
                    ],
                    "done_signal": "challenge shortlist、candidate 或 challenge manifest 至少推进一步，并让 latest 的 challenge_* 字段发生可观测变化。",
                    "when_to_refresh": "完成一轮 challenge 搜索、导入、筛选或接入动作后 refresh，确认 challenge 线是否重新出现 progress。",
                    "expected_tracking_signals": [
                        "changed_fields 包含 challenge_task_count、challenge_next_action 或 challenge_shortlist_candidate_count",
                        "refresh_outcome.category 不再只是 no_material_change",
                        "action_board 继续把 challenge 线保持在第一优先级，直到 shortlist 或 challenge manifest 发生推进",
                    ],
                },
                {
                    "priority": 2,
                    "track": "performance_track",
                    "reason": roadmap_focus.get("performance_track", {}).get("summary"),
                    "actions": [
                        "先补环境基线与公共任务时延对比，再决定是否继续下钻 run_tests / pytest startup。",
                    ],
                    "commands": [
                        "python scripts/snapshot_env_baseline.py --repetitions 10 --output-dir logs/env_baselines",
                        "python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_frozen40v68r1_001.json --improved-batch-summary logs/summaries/batch_run_frozen40v69r1_001.json --run-label frozen40_v68_v69",
                        "python scripts/refresh_roadmap_tracking.py --run-label refresh",
                    ],
                    "docs": [
                        "docs/v2_roadmap.md",
                        "docs/next_actions.md",
                        "docs/project_memory.md",
                    ],
                    "done_signal": "新增一轮稳定性、环境或时延证据，足以支持是否继续推进性能线。",
                    "when_to_refresh": "补完新的性能复核产物后 refresh，观察 history advice 是否升级或回退。",
                    "expected_tracking_signals": [
                        "logs/summaries 中新增 env baseline 或 duration compare 产物",
                        "history_advice.summary 对性能线的判断发生更新",
                        "recent_no_material_change_streak 被打断，或建议优先级发生调整",
                    ],
                },
            ]
        else:
            priorities = [
                {
                    "priority": 1,
                    "track": "performance_track",
                    "reason": roadmap_focus.get("performance_track", {}).get("summary"),
                    "actions": [
                        "先补环境基线与公共任务时延对比，再决定是否继续下钻 run_tests / pytest startup。",
                    ],
                    "commands": [
                        "python scripts/snapshot_env_baseline.py --repetitions 10 --output-dir logs/env_baselines",
                        "python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_frozen40v68r1_001.json --improved-batch-summary logs/summaries/batch_run_frozen40v69r1_001.json --run-label frozen40_v68_v69",
                        "python scripts/refresh_roadmap_tracking.py --run-label refresh",
                    ],
                    "docs": [
                        "docs/v2_roadmap.md",
                        "docs/next_actions.md",
                        "docs/project_memory.md",
                    ],
                    "done_signal": "新增一轮稳定性、环境或时延证据，足以支持是否继续推进性能线。",
                    "when_to_refresh": "补完新的性能复核产物后 refresh，观察 history advice 是否升级或回退。",
                    "expected_tracking_signals": [
                        "logs/summaries 中新增 env baseline 或 duration compare 产物",
                        "history_advice.summary 对性能线的判断发生更新",
                        "recent_no_material_change_streak 被打断，或建议优先级发生调整",
                    ],
                },
                {
                    "priority": 2,
                    "track": "formal_expansion_track",
                    "reason": roadmap_focus.get("formal_expansion_track", {}).get("summary"),
                    "actions": [
                        "维持正式集扩题节奏，把 gap 分析真正转成任务新增。",
                    ],
                    "commands": [
                        "python scripts/search_candidate_issues.py --target-family 并发与协程",
                    ],
                    "docs": [
                        "docs/issue_sourcing_brief_a2.md",
                        "docs/v2_roadmap.md",
                    ],
                    "done_signal": "候选池或正式任务集至少推进一步，例如 imported->screened、accepted->task、task->formal。",
                    "when_to_refresh": "完成候选或任务接入动作后 refresh，确认正式集与 candidate 口径变化。",
                    "expected_tracking_signals": [
                        "candidate_count、formal_task_count 或 ecosystem_count 至少有一个变化",
                        "refresh_outcome.category 不再只是 no_material_change",
                    ],
                },
            ]

    return {
        "created_at": _utc_timestamp(),
        "source_refresh_id": current_summary.get("refresh_id"),
        "headline": current_summary.get("headline"),
        "refresh_outcome": refresh_outcome,
        "history_advice": history_advice,
        "current_state": {
            "formal_task_count": current_state.get("formal_task_count"),
            "challenge_task_count": current_state.get("challenge_task_count"),
            "ecosystem_count": current_state.get("ecosystem_count"),
            "candidate_count": current_state.get("candidate_count"),
            "screened_candidate_count": current_state.get("screened_candidate_count"),
            "screened_with_task_count": current_state.get("screened_with_task_count"),
            "imported_candidate_count": current_state.get("imported_candidate_count"),
            "latest_frozen_task_count": current_state.get("latest_frozen_task_count"),
            "frozen_40_streak": current_state.get("frozen_40_streak"),
        },
        "challenge_status": {
            "shortlist_candidate_count": challenge_status.get("shortlist_candidate_count"),
            "next_candidate_issue_ref": challenge_status.get("next_candidate_issue_ref"),
            "next_action": challenge_status.get("next_action"),
            "local_auth_readiness": challenge_status.get("local_auth_readiness", {}),
        },
        "top_priorities": priorities,
    }


def build_status_card(current_summary: dict, history_summary: dict, action_board: dict) -> dict:
    current_state = action_board.get("current_state", {})
    top_priorities = action_board.get("top_priorities", [])
    top_priority = top_priorities[0] if top_priorities else {}
    history_advice = history_summary.get("advice", {})
    refresh_outcome = current_summary.get("refresh_outcome", {})

    return {
        "created_at": _utc_timestamp(),
        "source_refresh_id": current_summary.get("refresh_id"),
        "headline": current_summary.get("headline"),
        "refresh_outcome_category": refresh_outcome.get("category"),
        "history_advice_category": history_advice.get("category"),
        "history_advice_summary": history_advice.get("summary"),
        "recent_no_material_change_streak": history_summary.get("recent_no_material_change_streak"),
        "current_state": {
            "formal_task_count": current_state.get("formal_task_count"),
            "challenge_task_count": current_state.get("challenge_task_count"),
            "ecosystem_count": current_state.get("ecosystem_count"),
            "candidate_count": current_state.get("candidate_count"),
            "screened_candidate_count": current_state.get("screened_candidate_count"),
            "screened_with_task_count": current_state.get("screened_with_task_count"),
            "imported_candidate_count": current_state.get("imported_candidate_count"),
            "latest_frozen_task_count": current_state.get("latest_frozen_task_count"),
            "frozen_40_streak": current_state.get("frozen_40_streak"),
        },
        "challenge_status": {
            "shortlist_candidate_count": action_board.get("challenge_status", {}).get("shortlist_candidate_count"),
            "next_candidate_issue_ref": action_board.get("challenge_status", {}).get("next_candidate_issue_ref"),
            "local_auth_readiness": action_board.get("challenge_status", {}).get("local_auth_readiness", {}),
        },
        "top_priority": {
            "track": top_priority.get("track"),
            "reason": top_priority.get("reason"),
            "first_action": (top_priority.get("actions") or [None])[0],
            "first_command": (top_priority.get("commands") or [None])[0],
            "done_signal": top_priority.get("done_signal"),
            "when_to_refresh": top_priority.get("when_to_refresh"),
        },
    }


def build_status_card_markdown(status_card: dict) -> str:
    current_state = status_card["current_state"]
    challenge_status = status_card.get("challenge_status", {})
    local_auth_readiness = challenge_status.get("local_auth_readiness", {})
    top_priority = status_card["top_priority"]
    return f"""# Roadmap Status Card

- source_refresh_id: `{status_card["source_refresh_id"]}`
- headline: `{status_card["headline"]}`
- refresh_outcome_category: `{status_card["refresh_outcome_category"]}`
- history_advice_category: `{status_card["history_advice_category"]}`
- history_advice_summary: `{status_card["history_advice_summary"]}`
- recent_no_material_change_streak: `{status_card["recent_no_material_change_streak"]}`
- state: formal=`{current_state["formal_task_count"]}` challenge=`{current_state["challenge_task_count"]}` eco=`{current_state["ecosystem_count"]}` candidate=`{current_state["candidate_count"]}` screened=`{current_state["screened_candidate_count"]}` imported=`{current_state["imported_candidate_count"]}` frozen=`{current_state["latest_frozen_task_count"]}` streak=`{current_state["frozen_40_streak"]}`
- screened_with_task_count: `{current_state["screened_with_task_count"]}`
- challenge_shortlist_candidate_count: `{challenge_status.get("shortlist_candidate_count")}`
- challenge_next_candidate_issue_ref: `{challenge_status.get("next_candidate_issue_ref")}`
- challenge_auth_env_token_present: `{local_auth_readiness.get("env_token_present")}`
- challenge_auth_env_token_looks_valid: `{local_auth_readiness.get("env_token_looks_valid")}`
- challenge_auth_gh_logged_in: `{local_auth_readiness.get("gh_auth_logged_in")}`
- challenge_auth_token_exportable: `{local_auth_readiness.get("gh_auth_token_exportable")}`
- challenge_auth_preferred_search_mode: `{local_auth_readiness.get("preferred_search_mode")}`
- top_priority_track: `{top_priority.get("track")}`
- top_priority_reason: `{top_priority.get("reason")}`
- first_action: `{top_priority.get("first_action")}`
- first_command: `{top_priority.get("first_command")}`
- done_signal: `{top_priority.get("done_signal")}`
- when_to_refresh: `{top_priority.get("when_to_refresh")}`
"""


def build_action_board_markdown(action_board: dict) -> str:
    refresh_outcome = action_board["refresh_outcome"]
    history_advice = action_board["history_advice"]
    current_state = action_board["current_state"]
    challenge_status = action_board.get("challenge_status", {})
    local_auth_readiness = challenge_status.get("local_auth_readiness", {})
    priority_lines = "\n".join(
        "\n".join(
            [
                f"### Priority {item['priority']}: {item['track']}",
                f"- reason: {item['reason']}",
                *[f"- action: {action}" for action in item.get("actions", [])],
                *[f"- command: `{command}`" for command in item.get("commands", [])],
                *[f"- doc: `{doc}`" for doc in item.get("docs", [])],
                f"- done_signal: {item.get('done_signal')}",
                f"- when_to_refresh: {item.get('when_to_refresh')}",
                *[f"- expected_signal: {signal}" for signal in item.get("expected_tracking_signals", [])],
            ]
        )
        for item in action_board["top_priorities"]
    ) or "- 当前没有优先动作"

    return f"""# Roadmap Action Board

## Snapshot

- source_refresh_id: `{action_board["source_refresh_id"]}`
- headline: `{action_board["headline"]}`
- refresh_outcome: `{refresh_outcome.get("category")}` / {refresh_outcome.get("summary")}
- history_advice: `{history_advice.get("category")}` / {history_advice.get("summary")}

## Current State

- formal_task_count: `{current_state["formal_task_count"]}`
- challenge_task_count: `{current_state["challenge_task_count"]}`
- ecosystem_count: `{current_state["ecosystem_count"]}`
- candidate_count: `{current_state["candidate_count"]}`
- screened_candidate_count: `{current_state["screened_candidate_count"]}`
- imported_candidate_count: `{current_state["imported_candidate_count"]}`
- latest_frozen_task_count: `{current_state["latest_frozen_task_count"]}`
- frozen_40_streak: `{current_state["frozen_40_streak"]}`
- challenge_shortlist_candidate_count: `{challenge_status.get("shortlist_candidate_count")}`
- challenge_next_candidate_issue_ref: `{challenge_status.get("next_candidate_issue_ref")}`
- challenge_auth_env_token_present: `{local_auth_readiness.get("env_token_present")}`
- challenge_auth_env_token_looks_valid: `{local_auth_readiness.get("env_token_looks_valid")}`
- challenge_auth_gh_logged_in: `{local_auth_readiness.get("gh_auth_logged_in")}`
- challenge_auth_token_exportable: `{local_auth_readiness.get("gh_auth_token_exportable")}`
- challenge_auth_preferred_search_mode: `{local_auth_readiness.get("preferred_search_mode")}`

## Top Priorities

{priority_lines}
"""


def build_refresh_history_markdown(history_summary: dict) -> str:
    category_counts = history_summary["category_counts"]
    advice = history_summary.get("advice", {})
    category_lines = "\n".join(
        f"- {category}: `{count}`"
        for category, count in sorted(category_counts.items())
    ) or "- 当前没有历史记录"
    recent_entry_lines = "\n".join(
        f"- `{entry['refresh_id']}` | `{entry['outcome_category']}` | changed_fields=`{', '.join(entry['changed_fields']) or 'none'}` | headline=`{entry['headline']}`"
        for entry in history_summary["recent_entries"]
    ) or "- 当前没有 recent entries"
    recommended_actions = "\n".join(
        f"- {item}"
        for item in advice.get("recommended_actions", [])
    ) or "- 当前没有额外建议"

    return f"""# Roadmap Tracking History

## Overview

- run_label: `{history_summary["run_label"]}`
- latest_refresh_id: `{history_summary["latest_refresh_id"]}`
- total_refresh_count: `{history_summary["total_refresh_count"]}`
- recent_entry_count: `{history_summary["recent_entry_count"]}`
- recent_no_material_change_streak: `{history_summary["recent_no_material_change_streak"]}`

## Category Counts

{category_lines}

## Trend Advice

- category: `{advice.get("category")}`
- summary: `{advice.get("summary")}`
- recommended_focus: `{advice.get("recommended_focus")}`

### Recommended Actions

{recommended_actions}

## Recent Entries

{recent_entry_lines}
"""


def build_refresh_markdown(summary: dict) -> str:
    validation = summary["validation"]
    outputs = summary["outputs"]
    snapshot_summary = summary.get("snapshot_summary")
    changed_fields = summary.get("changed_fields", [])
    delta = summary.get("delta")
    refresh_outcome = summary.get("refresh_outcome", {})
    history_overview = summary.get("history_overview", {})
    previous_latest_summary_json_path = summary.get("previous_latest_summary_json_path")

    validation_errors = "\n".join(f"- {item}" for item in validation["errors"]) or "- 当前没有校验错误"
    changed_fields_text = ", ".join(changed_fields) if changed_fields else "none"
    delta_lines = "\n".join(
        f"- {item['field']}: `{item['previous']}` -> `{item['current']}`"
        for item in (delta or {}).get("field_changes", [])
    ) or "- 当前没有高信号字段变化"

    body = f"""# Roadmap Tracking Refresh

## Validation

- passed: `{validation["passed"]}`
- tasks_dir: `{validation["tasks_dir"]}`
- candidate_file: `{validation["candidate_file"]}`
- challenge_shortlist: `{validation["challenge_shortlist"]}`
- formal_manifest: `{validation["formal_manifest"]}`

### Validation Errors

{validation_errors}

## Outputs

- audit_summary_json_path: `{outputs["audit_summary_json_path"]}`
- maturity_summary_json_path: `{outputs["maturity_summary_json_path"]}`
- snapshot_summary_json_path: `{outputs["snapshot_summary_json_path"]}`
- history_summary_json_path: `{outputs.get("history_summary_json_path")}`
- history_summary_md_path: `{outputs.get("history_summary_md_path")}`
- action_board_json_path: `{outputs.get("action_board_json_path")}`
- action_board_md_path: `{outputs.get("action_board_md_path")}`
- status_card_json_path: `{outputs.get("status_card_json_path")}`
- status_card_md_path: `{outputs.get("status_card_md_path")}`
- headline: `{summary["headline"]}`

## Outcome

- category: `{refresh_outcome.get("category")}`
- summary: `{refresh_outcome.get("summary")}`

## History Overview

- total_refresh_count: `{history_overview.get("total_refresh_count")}`
- recent_no_material_change_streak: `{history_overview.get("recent_no_material_change_streak")}`
- history_category_counts: `{history_overview.get("category_counts")}`
- history_advice_category: `{history_overview.get("advice", {}).get("category")}`
- history_advice_summary: `{history_overview.get("advice", {}).get("summary")}`

## Fast Paths

- status_card: `适合 30 秒内接管当前状态`
- action_board: `适合直接开始执行下一步动作`
- history_summary: `适合回看最近几轮 refresh 趋势`

## Delta

- previous_latest_summary_json_path: `{previous_latest_summary_json_path}`
- changed_fields: `{changed_fields_text}`
- delta_change_count: `{(delta or {}).get("change_count", 0)}`

### Delta Details

{delta_lines}
"""

    if snapshot_summary is None:
        return body

    current_state = snapshot_summary["current_state"]
    challenge_status = snapshot_summary["challenge_status"]
    candidate_count = current_state.get("candidate_count", "unknown")
    screened_candidate_count = current_state.get("screened_candidate_count", "unknown")
    screened_with_task_count = current_state.get("screened_with_task_count", "unknown")
    imported_candidate_count = current_state.get("imported_candidate_count", "unknown")
    latest_frozen_task_count = current_state.get("latest_frozen_task_count", "unknown")
    frozen_40_streak = current_state.get("frozen_40_streak", "unknown")
    next_action = challenge_status.get("next_action", "unknown")
    shortlist_candidate_count = challenge_status.get("shortlist_candidate_count", "unknown")
    next_candidate_issue_ref = challenge_status.get("next_candidate_issue_ref", "unknown")
    return (
        body
        + f"""

## Snapshot Highlights

- formal_task_count: `{current_state["formal_task_count"]}`
- challenge_task_count: `{current_state["challenge_task_count"]}`
- ecosystem_count: `{current_state["ecosystem_count"]}`
- candidate_count: `{candidate_count}`
- screened_candidate_count: `{screened_candidate_count}`
- screened_with_task_count: `{screened_with_task_count}`
- imported_candidate_count: `{imported_candidate_count}`
- latest_frozen_task_count: `{latest_frozen_task_count}`
- frozen_40_streak: `{frozen_40_streak}`
- challenge_shortlist_candidate_count: `{shortlist_candidate_count}`
- challenge_next_candidate_issue_ref: `{next_candidate_issue_ref}`
- challenge_next_action: `{next_action}`
"""
    )


def refresh_roadmap_tracking(
    *,
    repo_root: Path = REPO_ROOT,
    tasks_dir: str | Path = "benchmarks/tasks",
    candidate_file: str | Path = "benchmarks/real_world_candidates.json",
    challenge_shortlist: str | Path = "docs/challenge_shortlist.md",
    formal_manifest: str | Path = "benchmarks/manifests/real_issue_tasks.json",
    challenge_manifest: str | Path = "benchmarks/manifests/real_issue_tasks_challenge_v1.json",
    frozen_manifest_glob: str = "real_issue_tasks_frozen_*_v1.json",
    output_dir: str | Path = "logs/summaries",
    run_label: str | None = None,
) -> dict:
    output_directory = (repo_root / output_dir).resolve() if not Path(output_dir).is_absolute() else Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    resolved_tasks_dir = (repo_root / tasks_dir).resolve() if not Path(tasks_dir).is_absolute() else Path(tasks_dir).resolve()
    resolved_candidate_file = (repo_root / candidate_file).resolve() if not Path(candidate_file).is_absolute() else Path(candidate_file).resolve()
    resolved_challenge_shortlist = (repo_root / challenge_shortlist).resolve() if not Path(challenge_shortlist).is_absolute() else Path(challenge_shortlist).resolve()
    resolved_formal_manifest = (repo_root / formal_manifest).resolve() if not Path(formal_manifest).is_absolute() else Path(formal_manifest).resolve()
    resolved_challenge_manifest = (repo_root / challenge_manifest).resolve() if not Path(challenge_manifest).is_absolute() else Path(challenge_manifest).resolve()

    validation_errors = validate_repository(
        repo_root=repo_root,
        tasks_dir=resolved_tasks_dir,
        candidate_file=resolved_candidate_file,
        challenge_shortlist_path=resolved_challenge_shortlist,
        formal_manifest_path=resolved_formal_manifest,
    )

    refresh_id = _next_refresh_id(output_directory, run_label=run_label)
    summary_json_path = output_directory / f"{refresh_id}.json"
    summary_md_path = output_directory / f"{refresh_id}.md"
    latest_json_path, latest_md_path = _latest_output_paths(output_directory, run_label=run_label)
    history_json_path, history_md_path = _history_output_paths(output_directory, run_label=run_label)
    action_board_json_path, action_board_md_path = _action_board_output_paths(output_directory, run_label=run_label)
    status_card_json_path, status_card_md_path = _status_card_output_paths(output_directory, run_label=run_label)

    validation_summary = {
        "passed": not validation_errors,
        "errors": validation_errors,
        "tasks_dir": str(resolved_tasks_dir),
        "candidate_file": str(resolved_candidate_file),
        "challenge_shortlist": str(resolved_challenge_shortlist),
        "formal_manifest": str(resolved_formal_manifest),
    }
    previous_summary = _load_previous_summary(latest_json_path)
    previous_latest_summary_json_path = str(latest_json_path) if previous_summary is not None else None

    # 如果基础校验都没过，就先停止刷新，避免把后续产物建立在错误状态上。
    if validation_errors:
        summary = {
            "created_at": _utc_timestamp(),
            "refresh_id": refresh_id,
            "validation": validation_summary,
            "outputs": {
                "audit_summary_json_path": None,
                "maturity_summary_json_path": None,
                "snapshot_summary_json_path": None,
                "history_summary_json_path": str(history_json_path),
                "history_summary_md_path": str(history_md_path),
                "action_board_json_path": str(action_board_json_path),
                "action_board_md_path": str(action_board_md_path),
                "status_card_json_path": str(status_card_json_path),
                "status_card_md_path": str(status_card_md_path),
            },
            "headline": "roadmap: validation=FAIL",
            "snapshot_summary": None,
            "previous_latest_summary_json_path": previous_latest_summary_json_path,
            "changed_fields": [],
            "delta": None,
        }
        changed_fields, delta = build_refresh_delta(previous_summary, summary)
        summary["changed_fields"] = changed_fields
        summary["delta"] = delta
        summary["refresh_outcome"] = build_refresh_outcome(previous_summary, summary, changed_fields, delta)
        history_summary = build_refresh_history(
            summary_dir=output_directory,
            run_label=run_label,
            current_summary=summary,
            current_summary_json_path=summary_json_path,
        )
        history_summary["advice"] = build_history_advice(history_summary, summary)
        summary["history_overview"] = {
            "total_refresh_count": history_summary["total_refresh_count"],
            "recent_no_material_change_streak": history_summary["recent_no_material_change_streak"],
            "category_counts": history_summary["category_counts"],
            "advice": history_summary["advice"],
        }
        action_board = build_action_board(summary, history_summary)
        status_card = build_status_card(summary, history_summary, action_board)
        write_json(summary_json_path, summary)
        write_json(history_json_path, history_summary)
        write_json(action_board_json_path, action_board)
        write_json(status_card_json_path, status_card)
        write_text(summary_md_path, build_refresh_markdown(summary))
        write_text(history_md_path, build_refresh_history_markdown(history_summary))
        write_text(action_board_md_path, build_action_board_markdown(action_board))
        write_text(status_card_md_path, build_status_card_markdown(status_card))
        write_json(latest_json_path, summary)
        write_text(latest_md_path, build_refresh_markdown(summary))
        return {
            "refresh_id": refresh_id,
            "summary": summary,
            "summary_json_path": str(summary_json_path),
            "summary_md_path": str(summary_md_path),
            "latest_summary_json_path": str(latest_json_path),
            "latest_summary_md_path": str(latest_md_path),
            "history_summary_json_path": str(history_json_path),
            "history_summary_md_path": str(history_md_path),
            "action_board_json_path": str(action_board_json_path),
            "action_board_md_path": str(action_board_md_path),
            "status_card_json_path": str(status_card_json_path),
            "status_card_md_path": str(status_card_md_path),
        }

    audit_output = audit_semi_real_pipeline(
        candidate_file=resolved_candidate_file,
        tasks_dir=resolved_tasks_dir,
        formal_manifest=resolved_formal_manifest,
        challenge_manifest=resolved_challenge_manifest,
        output_dir=output_directory,
        run_label=run_label or "refresh",
    )
    maturity_output = analyze_benchmark_maturity(
        repo_root=repo_root,
        formal_manifest=resolved_formal_manifest,
        challenge_manifest=resolved_challenge_manifest,
        candidate_file=resolved_candidate_file,
        frozen_manifest_glob=frozen_manifest_glob,
        output_dir=output_directory,
        run_label=run_label or "refresh",
    )
    snapshot_output = snapshot_roadmap_status(
        repo_root=repo_root,
        formal_manifest=resolved_formal_manifest,
        challenge_manifest=resolved_challenge_manifest,
        candidate_file=resolved_candidate_file,
        frozen_manifest_glob=frozen_manifest_glob,
        tasks_dir=resolved_tasks_dir,
        output_dir=output_directory,
        run_label=run_label or "refresh",
    )

    summary = {
        "created_at": _utc_timestamp(),
        "refresh_id": refresh_id,
        "validation": validation_summary,
        "outputs": {
            "audit_summary_json_path": audit_output["summary_json_path"],
            "maturity_summary_json_path": maturity_output["summary_json_path"],
            "snapshot_summary_json_path": snapshot_output["summary_json_path"],
            "history_summary_json_path": str(history_json_path),
            "history_summary_md_path": str(history_md_path),
            "action_board_json_path": str(action_board_json_path),
            "action_board_md_path": str(action_board_md_path),
            "status_card_json_path": str(status_card_json_path),
            "status_card_md_path": str(status_card_md_path),
        },
        "headline": build_tracking_headline(
            snapshot_output["summary"],
            validation_passed=True,
        ),
        "snapshot_summary": snapshot_output["summary"],
        "previous_latest_summary_json_path": previous_latest_summary_json_path,
    }
    changed_fields, delta = build_refresh_delta(previous_summary, summary)
    summary["changed_fields"] = changed_fields
    summary["delta"] = delta
    summary["refresh_outcome"] = build_refresh_outcome(previous_summary, summary, changed_fields, delta)
    history_summary = build_refresh_history(
        summary_dir=output_directory,
        run_label=run_label,
        current_summary=summary,
        current_summary_json_path=summary_json_path,
    )
    history_summary["advice"] = build_history_advice(history_summary, summary)
    summary["history_overview"] = {
        "total_refresh_count": history_summary["total_refresh_count"],
        "recent_no_material_change_streak": history_summary["recent_no_material_change_streak"],
        "category_counts": history_summary["category_counts"],
        "advice": history_summary["advice"],
    }
    action_board = build_action_board(summary, history_summary)
    status_card = build_status_card(summary, history_summary, action_board)
    write_json(summary_json_path, summary)
    write_json(history_json_path, history_summary)
    write_json(action_board_json_path, action_board)
    write_json(status_card_json_path, status_card)
    write_text(summary_md_path, build_refresh_markdown(summary))
    write_text(history_md_path, build_refresh_history_markdown(history_summary))
    write_text(action_board_md_path, build_action_board_markdown(action_board))
    write_text(status_card_md_path, build_status_card_markdown(status_card))
    write_json(latest_json_path, summary)
    write_text(latest_md_path, build_refresh_markdown(summary))

    return {
        "refresh_id": refresh_id,
        "summary": summary,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "latest_summary_json_path": str(latest_json_path),
        "latest_summary_md_path": str(latest_md_path),
        "history_summary_json_path": str(history_json_path),
        "history_summary_md_path": str(history_md_path),
        "action_board_json_path": str(action_board_json_path),
        "action_board_md_path": str(action_board_md_path),
        "status_card_json_path": str(status_card_json_path),
        "status_card_md_path": str(status_card_md_path),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="一键刷新 roadmap 持续追踪的关键产物。")
    parser.add_argument("--tasks-dir", default="benchmarks/tasks", help="任务目录")
    parser.add_argument("--candidate-file", default="benchmarks/real_world_candidates.json", help="候选池文件")
    parser.add_argument("--challenge-shortlist", default="docs/challenge_shortlist.md", help="challenge shortlist 文档路径")
    parser.add_argument("--formal-manifest", default="benchmarks/manifests/real_issue_tasks.json", help="正式主集 manifest 路径")
    parser.add_argument("--challenge-manifest", default="benchmarks/manifests/real_issue_tasks_challenge_v1.json", help="challenge manifest 路径")
    parser.add_argument("--frozen-manifest-glob", default="real_issue_tasks_frozen_*_v1.json", help="冻结 manifest 的 glob 模式")
    parser.add_argument("--output-dir", default="logs/summaries", help="输出目录")
    parser.add_argument("--run-label", default=None, help="可选标签，例如 refresh")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = refresh_roadmap_tracking(
        repo_root=REPO_ROOT,
        tasks_dir=args.tasks_dir,
        candidate_file=args.candidate_file,
        challenge_shortlist=args.challenge_shortlist,
        formal_manifest=args.formal_manifest,
        challenge_manifest=args.challenge_manifest,
        frozen_manifest_glob=args.frozen_manifest_glob,
        output_dir=args.output_dir,
        run_label=args.run_label,
    )
    summary = output["summary"]
    print(f"refresh_id: {output['refresh_id']}")
    print(f"headline: {summary['headline']}")
    print(f"validation_passed: {summary['validation']['passed']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"latest_summary_json_path: {output['latest_summary_json_path']}")
    return 0 if summary["validation"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
