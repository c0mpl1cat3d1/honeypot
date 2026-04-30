from core.filesystem import FileSystem


VALID_FLAGS = set("frR")


def run(args, current_directory):
    if not args:
        return "rm: missing operand"

    options, paths, error = parse_args(args)
    if error:
        return error

    if not paths:
        return "rm: missing operand"

    fs = FileSystem()
    output = []

    for path in paths:
        _, error = fs.remove(
            current_directory,
            path,
            recursive=options["recursive"],
            force=options["force"],
        )
        if error:
            output.append(error)

    return "\n".join(output)


def parse_args(args):
    options = {"force": False, "recursive": False}
    paths = []

    for index, arg in enumerate(args):
        if arg == "--":
            paths.extend(args[index + 1 :])
            break

        if arg == "--help":
            return options, paths, "\n".join(
                [
                    "Usage: rm [OPTION]... [FILE]...",
                    "Remove files or directories.",
                    "  -f        ignore nonexistent files",
                    "  -r, -R    remove directories and their contents recursively",
                ]
            )

        if arg.startswith("-") and arg != "-":
            for flag in arg[1:]:
                if flag not in VALID_FLAGS:
                    return options, paths, f"rm: invalid option -- '{flag}'"
                if flag == "f":
                    options["force"] = True
                elif flag in ("r", "R"):
                    options["recursive"] = True
            continue

        paths.append(arg)

    return options, paths, None
