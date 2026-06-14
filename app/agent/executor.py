"""Agent 执行器。"""

from pathlib import Path

from app.agent.llm_agent import LLMCodeAgent
from app.agent.policy import load_policy_config
from app.agent.rule_based_agent import RuleBasedAgent


def run_agent(task_path: str | Path, repo_root: str | Path, policy_path: str | Path | None = None) -> dict:
    # 当前根据 policy 选择规则版 baseline 或 LLM agent。
    policy_config = load_policy_config(policy_path)
    if policy_config.agent_type == "llm":
        agent = LLMCodeAgent()
    else:
        agent = RuleBasedAgent()
    return agent.run(task_path=task_path, repo_root=repo_root, policy_path=policy_path)
