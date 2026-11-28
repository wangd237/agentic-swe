"""Regression for applying patches to evaluator copies nested below a Git worktree."""
import pathlib
import tempfile

from validate import apply


def test_apply_targets_nested_copy_not_parent_worktree():
    patch_text = (
        "diff --git a/admission_patch_probe.txt b/admission_patch_probe.txt\n"
        "new file mode 100644\n"
        "--- /dev/null\n"
        "+++ b/admission_patch_probe.txt\n"
        "@@ -0,0 +1 @@\n"
        "+applied\n"
    )
    with tempfile.TemporaryDirectory(dir=pathlib.Path.cwd()) as td:
        private = pathlib.Path(td)
        repo = private / "copy"
        repo.mkdir()
        patch = private / "candidate.patch"
        patch.write_text(patch_text, encoding="utf-8")
        apply(repo, patch)
        assert (repo / "admission_patch_probe.txt").read_text() == "applied\n"
        assert not (pathlib.Path.cwd() / "admission_patch_probe.txt").exists()
