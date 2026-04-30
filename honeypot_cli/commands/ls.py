import datetime
import hashlib
import posixpath

from core.filesystem import FileSystem


VALID_FLAGS = set("1AadFhl")
LONG_OPTIONS = {
    "--all": "a",
    "--almost-all": "A",
    "--classify": "F",
    "--directory": "d",
    "--human-readable": "h",
    "--long": "l",
    "--help": "help",
}


def run(args, current_directory, context=None):
    context = context or {}
    fs = context.get("fs") or FileSystem()
    options, paths, error = parse_args(args)

    if error:
        return error

    if options.get("help"):
        return "\n".join(
            [
                "Usage: ls [OPTION]... [FILE]...",
                "List information about the FILEs (the current directory by default).",
                "  -a, --all            do not ignore entries starting with .",
                "  -A, --almost-all     do not list implied . and ..",
                "  -d, --directory      list directories themselves, not their contents",
                "  -F, --classify       append indicator (one of */=>@|) to entries",
                "  -h, --human-readable with -l, print sizes in human readable format",
                "  -l, --long           use a long listing format",
                "  -1                   list one file per line",
            ]
        )

    paths = paths or ["."]
    output = []
    multiple_paths = len(paths) > 1

    for path in paths:
        node, absolute_path = resolve_path(fs, current_directory, path, context)

        if node is None:
            output.append(f"ls: cannot access '{path}': No such file or directory")
            continue

        if isinstance(node, dict) and not options["d"]:
            if multiple_paths:
                if output:
                    output.append("")
                output.append(f"{path}:")

            listing = list_directory(node, absolute_path, options, context)
            if listing:
                output.append(listing)
            continue

        name = posixpath.basename(absolute_path.rstrip("/")) or "/"
        output.append(format_entries([(name, node, absolute_path)], options, context, include_total=False))

    return "\n".join(output)


def parse_args(args):
    options = {"1": False, "A": False, "F": False, "a": False, "d": False, "h": False, "l": False}
    paths = []

    for index, arg in enumerate(args):
        if arg == "--":
            paths.extend(args[index + 1 :])
            break

        if arg.startswith("--"):
            flag = LONG_OPTIONS.get(arg)
            if flag is None:
                return options, paths, f"ls: unrecognized option '{arg}'"
            if flag == "help":
                options["help"] = True
            else:
                options[flag] = True
            continue

        if arg.startswith("-") and arg != "-":
            for flag in arg[1:]:
                if flag not in VALID_FLAGS:
                    return options, paths, f"ls: invalid option -- '{flag}'"
                options[flag] = True
            continue

        paths.append(arg)

    if options["a"]:
        options["A"] = False

    return options, paths, None


def resolve_path(fs, current_directory, path, context):
    home_directory = context.get("home_directory", "/home/guest")

    if path == "~":
        full_path = home_directory
    elif path.startswith("~/"):
        full_path = posixpath.join(home_directory, path[2:])
    elif path.startswith("/"):
        full_path = path
    else:
        full_path = posixpath.join(current_directory, path)

    full_path = posixpath.normpath(full_path)
    if not full_path.startswith("/"):
        full_path = "/" + full_path

    node = fs.fs.get("/")
    if full_path == "/":
        return node, full_path

    for part in [part for part in full_path.split("/") if part]:
        if not isinstance(node, dict) or part not in node:
            return None, full_path
        node = node[part]

    return node, full_path


def list_directory(directory, absolute_path, options, context):
    entries = []

    if options["a"]:
        entries.extend(
            [
                (".", directory, absolute_path),
                ("..", {}, parent_path(absolute_path)),
            ]
        )

    for name in sorted(directory):
        if name.startswith(".") and not (options["a"] or options["A"]):
            continue
        entries.append((name, directory[name], posixpath.join(absolute_path, name)))

    return format_entries(entries, options, context)


def format_entries(entries, options, context, include_total=True):
    if options["l"]:
        return format_long(entries, options, context, include_total)

    names = [display_name(name, node, options) for name, node, _ in entries]
    if options["1"]:
        return "\n".join(names)

    return format_columns(names)


def format_columns(names):
    if not names:
        return ""

    width = max(len(name) for name in names) + 2
    columns = max(1, 80 // width)
    lines = []

    for index in range(0, len(names), columns):
        row = names[index : index + columns]
        lines.append("".join(name.ljust(width) for name in row).rstrip())

    return "\n".join(lines)


def format_long(entries, options, context, include_total):
    lines = []

    if include_total:
        total = sum(blocks_for(node) for _, node, _ in entries)
        lines.append(f"total {total}")

    for name, node, path in entries:
        lines.append(long_line(name, node, path, options, context))

    return "\n".join(lines)


def long_line(name, node, path, options, context):
    is_dir = isinstance(node, dict)
    permissions = "drwxr-xr-x" if is_dir else "-rw-r--r--"
    links = 2 if is_dir else 1
    owner = context.get("username", "guest")
    group = owner
    size = directory_size(node) if is_dir else len(str(node).encode())
    displayed_size = human_size(size) if options["h"] else str(size)
    modified = fake_mtime(path)
    shown_name = display_name(name, node, options)

    return f"{permissions} {links:>2} {owner:<8} {group:<8} {displayed_size:>6} {modified} {shown_name}"


def display_name(name, node, options):
    if options["F"] and isinstance(node, dict) and name not in (".", "..", "/"):
        return f"{name}/"
    return name


def blocks_for(node):
    size = directory_size(node) if isinstance(node, dict) else len(str(node).encode())
    return max(4, ((size + 1023) // 1024) * 4)


def directory_size(node):
    return 4096 if isinstance(node, dict) else len(str(node).encode())


def human_size(size):
    units = ["B", "K", "M", "G"]
    value = float(size)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return str(int(value))
            return f"{value:.1f}{unit}".replace(".0", "")
        value /= 1024

    return str(size)


def fake_mtime(path):
    digest = hashlib.sha1(path.encode()).hexdigest()
    days_back = int(digest[:4], 16) % 365
    minutes = int(digest[4:8], 16) % (24 * 60)
    dt = datetime.datetime(2024, 6, 1, 12, 0) - datetime.timedelta(
        days=days_back,
        minutes=minutes,
    )
    return dt.strftime("%b %e %H:%M")


def parent_path(path):
    if path == "/":
        return "/"
    return posixpath.dirname(path.rstrip("/")) or "/"
