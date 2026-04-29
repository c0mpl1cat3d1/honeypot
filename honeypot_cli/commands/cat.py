from core.filesystem import FileSystem


def run(args, current_directory):
    if not args:
        return "cat: missing file operand"

    fs = FileSystem()
    output = []

    for filename in args:
        node = fs.resolve_path(current_directory, filename)

        if node is None:
            output.append(f"cat: {filename}: No such file or directory")
        elif isinstance(node, dict):
            output.append(f"cat: {filename}: Is a directory")
        else:
            output.append(node.rstrip("\n"))

    return "\n".join(output)
