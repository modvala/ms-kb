import re
from datetime import date

import pytest

from ms_kb.vault import NOTE_TEMPLATES, VAULT_DIRS, check_vault, git_work_tree, init_vault

# note-schema-v0 §1–§2
COMMON_FIELDS = {"type", "title", "created", "updated", "topics"}
TYPE_FIELDS = {
    "concept": set(),
    "source": {"url"},
    "research": {"as_of", "sources"},
    "learning-session": {"session_date"},
    "project": set(),
}


def frontmatter_keys(text: str) -> dict[str, str]:
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert match, "no frontmatter"
    return dict(re.findall(r"^([a-z_]+):\s*(.*)$", match.group(1), re.M))


def test_fresh_init_creates_everything(tmp_path):
    vault = tmp_path / "vault"
    report = init_vault(vault)
    assert all(status == "created" for _, status in report)
    for d in VAULT_DIRS:
        assert (vault / d).is_dir()
    for t in NOTE_TEMPLATES:
        assert (vault / "templates" / f"{t}.md").is_file()
    assert (vault / "README.md").is_file()
    profile = (vault / "learning_profile.md").read_text()
    assert f'updated: "{date.today().isoformat()}"' in profile
    assert check_vault(vault) == []


def test_second_init_changes_nothing(tmp_path):
    vault = tmp_path / "vault"
    init_vault(vault)
    (vault / "learning_profile.md").write_text("my profile")
    (vault / "templates" / "concept.md").write_text("my template")
    report = init_vault(vault)
    assert all(status == "exists" for _, status in report)
    assert (vault / "learning_profile.md").read_text() == "my profile"
    assert (vault / "templates" / "concept.md").read_text() == "my template"


def test_init_existing_folder_keeps_user_files(tmp_path):
    vault = tmp_path / "vault"
    (vault / "concepts").mkdir(parents=True)
    (vault / "concepts" / "RAG.md").write_text("mine")
    (vault / "notes.txt").write_text("other")
    init_vault(vault)
    assert (vault / "concepts" / "RAG.md").read_text() == "mine"
    assert (vault / "notes.txt").read_text() == "other"
    assert check_vault(vault) == []


def test_check_vault_reports_missing(tmp_path):
    vault = tmp_path / "vault"
    init_vault(vault)
    (vault / "learning_profile.md").unlink()
    (vault / "attachments").rmdir()
    assert sorted(check_vault(vault)) == ["attachments/", "learning_profile.md"]


@pytest.mark.parametrize("note_type", NOTE_TEMPLATES)
def test_template_frontmatter(tmp_path, note_type):
    init_vault(tmp_path)
    text = (tmp_path / "templates" / f"{note_type}.md").read_text()
    keys = frontmatter_keys(text)
    assert keys["type"] == note_type
    assert COMMON_FIELDS | TYPE_FIELDS[note_type] <= keys.keys()
    assert "created_by" not in keys  # hand-written notes carry no provenance


def test_templates_show_mermaid_and_attachments(tmp_path):
    init_vault(tmp_path)
    concept = (tmp_path / "templates" / "concept.md").read_text()
    assert "```mermaid" in concept
    assert "![[" in concept


def test_git_work_tree(tmp_path):
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    assert git_work_tree(tmp_path / "repo" / "vault") == tmp_path / "repo"
    assert git_work_tree(tmp_path / "elsewhere") != tmp_path / "repo"
