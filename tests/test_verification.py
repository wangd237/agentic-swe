from __future__ import annotations

from app.agent.verification import (
    adjust_final_status_for_verification,
    build_targeted_pytest_command,
    extract_pytest_node_ids,
    initial_verification_strength,
    strength_after_test,
)


def test_initial_verification_strength_detects_pytest_fallback() -> None:
    assert initial_verification_strength({"test_command_source": "pytest_fallback"}) == "weak"
    assert initial_verification_strength({"verification_strength": "weak"}) == "weak"
    assert initial_verification_strength({"test_command_source": "explicit"}) == "none"


def test_strength_after_test_preserves_weak_fallback() -> None:
    assert (
        strength_after_test(
            current="weak",
            exit_code=0,
            workspace_generation=1,
            command_source="pytest_fallback",
        )
        == "weak"
    )


def test_strength_after_test_marks_full_after_patch_with_real_command() -> None:
    assert (
        strength_after_test(
            current="targeted",
            exit_code=0,
            workspace_generation=1,
            command_source="explicit",
        )
        == "full"
    )


def test_adjust_final_status_downgrades_weak_success() -> None:
    final_status, incomplete_reason = adjust_final_status_for_verification(
        final_status="success",
        incomplete_reason="",
        verification_strength="weak",
        patch_applied=True,
    )

    assert final_status == "success_weak_verification"
    assert incomplete_reason == "weak_verification"


def test_adjust_final_status_keeps_full_success() -> None:
    final_status, incomplete_reason = adjust_final_status_for_verification(
        final_status="success",
        incomplete_reason="",
        verification_strength="full",
        patch_applied=True,
    )

    assert final_status == "success"
    assert incomplete_reason == ""


def test_extract_pytest_node_ids_strips_failure_detail() -> None:
    node_ids = extract_pytest_node_ids(
        {
            "failed_tests": [
                "tests/test_app.py::test_value - assert 1 == 2",
                "tests/test_app.py::TestThing::test_method - ValueError: bad",
                "not a node id",
                "tests/test_app.py::test_value - duplicate",
            ]
        }
    )

    assert node_ids == [
        "tests/test_app.py::test_value",
        "tests/test_app.py::TestThing::test_method",
    ]


def test_build_targeted_pytest_command_from_failure_summary() -> None:
    command = build_targeted_pytest_command(
        base_command='python -m pytest tests -q',
        failure_summary={
            "failed_tests": [
                "tests/test_app.py::test_value - assert 1 == 2",
                "tests/test_other.py::test_other - assert False",
            ]
        },
    )

    assert command == "python -m pytest tests/test_app.py::test_value tests/test_other.py::test_other -q"


def test_build_targeted_pytest_command_preserves_quoted_python_module_prefix() -> None:
    command = build_targeted_pytest_command(
        base_command='"C:\\Program Files\\Python313\\python.exe" -m pytest tests/test_app.py -q',
        failure_summary={
            "failed_tests": [
                "tests\\test_app.py::test_value - assert 1 == 2",
            ]
        },
    )

    assert command == '"C:\\Program Files\\Python313\\python.exe" -m pytest tests/test_app.py::test_value -q'


def test_build_targeted_pytest_command_requires_pytest_command() -> None:
    assert (
        build_targeted_pytest_command(
            base_command="python -m unittest",
            failure_summary={"failed_tests": ["tests/test_app.py::test_value - assert 1 == 2"]},
        )
        is None
    )
