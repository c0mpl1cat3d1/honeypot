import posixpath
import time

from commands._transfer import basename_from_source, human_size, progress_bar, safe_payload, transfer_size_bytes
from core.filesystem import FileSystem


def run(args, current_directory, context=None):
    if not args:
        return "usage: git [--version] [--help] <command> [<args>]"

    command = args[0]
    if command in ("--help", "-h", "help"):
        return "usage: git <command> [<args>]\n\nCommon commands: clone, pull, status, config"
    if command == "--version":
        return "git version 2.25.1"
    if command == "clone":
        return clone(args[1:], current_directory)
    if command == "pull":
        return "Already up to date."
    if command == "status":
        return "On branch main\nnothing to commit, working tree clean"
    if command == "config":
        return ""

    return f"git: '{command}' is not a git command. See 'git --help'."


def clone(args, current_directory):
    if not args:
        return "fatal: You must specify a repository to clone."

    repo_url = None
    destination = None
    for arg in args:
        if arg.startswith("-"):
            continue
        if repo_url is None:
            repo_url = arg
        elif destination is None:
            destination = arg

    if repo_url is None:
        return "fatal: You must specify a repository to clone."

    repo_name = destination or repository_name(repo_url)
    fs = FileSystem()
    ok, error = fs.mkdir(current_directory, repo_name)
    if not ok:
        return f"fatal: destination path '{repo_name}' already exists and is not an empty directory."

    fs.write_file(current_directory, posixpath.join(repo_name, "README.md"), safe_payload(repo_url))
    fs.write_file(current_directory, posixpath.join(repo_name, ".gitignore"), "*.log\n")

    total_objects = 18 + (sum(ord(ch) for ch in repo_url) % 70)
    total_bytes = transfer_size_bytes(repo_url, min_kb=120, max_kb=6800)

    lines = [f"Cloning into '{repo_name}'..."]
    time.sleep(0.15)
    lines.append(f"remote: Enumerating objects: {total_objects}, done.")
    time.sleep(0.2)

    for pct in (12, 28, 47, 66, 83, 100):
        counted = max(1, int(total_objects * pct / 100))
        lines.append(f"remote: Counting objects: {pct}% ({counted}/{total_objects})")
        if pct < 100:
            time.sleep(0.1)
    lines[-1] += ", done."

    for pct in (8, 22, 39, 57, 74, 91, 100):
        received = max(1, int(total_objects * pct / 100))
        bytes_done = int(total_bytes * pct / 100)
        rate = 180 + (pct * 3)
        lines.append(
            f"Receiving objects: {pct}% ({received}/{total_objects}), "
            f"{human_size(bytes_done)} | {rate}.00 KiB/s"
        )
        if pct < 100:
            time.sleep(0.14)
    lines[-1] += ", done."

    for pct in (25, 50, 75, 100):
        bars = progress_bar(pct, width=18).replace(" ", ".")
        deltas = max(1, int((total_objects // 4) * pct / 100))
        lines.append(f"Resolving deltas: {pct}% ({deltas}/{max(total_objects // 4, 1)}) [{bars}]")
        if pct < 100:
            time.sleep(0.12)
    lines[-1] += ", done."

    return "\n".join(lines)


def repository_name(repo_url):
    name = basename_from_source(repo_url, "repo")
    if name.endswith(".git"):
        name = name[:-4]
    return name or "repo"
