"""The safety checks matter more than anything else in Q, so they get the most tests."""

import os

import pytest

from q import tools


@pytest.fixture
def root(tmp_path):
    work = tmp_path / "work"
    (work / "notes").mkdir(parents=True)
    (work / "notes" / "os.md").write_text("Deadlock needs four conditions.\nMutual exclusion.\n")
    (work / "readme.txt").write_text("hello\n")
    (tmp_path / "secret.txt").write_text("outside the root\n")
    tools.set_root(work)
    return work


def test_read_file_inside_root(root):
    assert "four conditions" in tools.read_file("notes/os.md")


@pytest.mark.parametrize("bad", ["../secret.txt", "notes/../../secret.txt", "/etc/passwd"])
def test_paths_outside_root_are_refused(root, bad):
    with pytest.raises(tools.ToolError, match="Refused"):
        tools.read_file(bad)


@pytest.mark.skipif(os.name == "nt", reason="symlinks need admin rights on Windows")
def test_symlink_escape_is_refused(root):
    (root / "link.txt").symlink_to(root.parent / "secret.txt")
    with pytest.raises(tools.ToolError, match="Refused"):
        tools.read_file("link.txt")


@pytest.mark.skipif(os.name == "nt", reason="symlinks need admin rights on Windows")
def test_search_skips_symlinks_pointing_outside(root):
    (root / "link.txt").symlink_to(root.parent / "secret.txt")
    assert "outside the root" not in tools.search_files("outside")


def test_list_dir_shows_folders_first(root):
    assert tools.list_dir().splitlines() == ["notes/", "readme.txt"]


def test_list_dir_outside_root_refused(root):
    with pytest.raises(tools.ToolError):
        tools.list_dir("..")


def test_search_files_finds_line_numbers(root):
    out = tools.search_files("mutual")
    assert out == os.path.join("notes", "os.md") + ":2: Mutual exclusion."


def test_search_no_match(root):
    assert "No matches" in tools.search_files("zebra")


def test_output_is_capped(root):
    (root / "big.txt").write_text("x" * 50_000)
    assert len(tools.read_file("big.txt")) == tools.MAX_TOOL_OUTPUT
