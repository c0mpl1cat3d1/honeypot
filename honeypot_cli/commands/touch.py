from core.filesystem import FileSystem


def run(args, current_directory):
    if not args:
        return "touch: missing file operand"

    fs = FileSystem()
    output = []

    for path in args:
        if path.startswith("-"):
            output.append(f"touch: invalid option -- '{path[1:2]}'")
            continue

        _, error = fs.touch(current_directory, path)
        if error:
            output.append(error)

    return "\n".join(output)
