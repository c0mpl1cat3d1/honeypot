import posixpath


def run(args, current_directory, context=None):
    home_directory = (context or {}).get("home_directory", "/home/guest")
    target = args[0] if args else home_directory

    if target == "~":
        new_directory = home_directory
    elif target.startswith("~/"):
        new_directory = posixpath.join(home_directory, target[2:])
    elif target.startswith("/"):
        new_directory = target
    else:
        new_directory = posixpath.join(current_directory, target)

    new_directory = posixpath.normpath(new_directory)
    if not new_directory.startswith("/"):
        new_directory = "/" + new_directory

    return {"current_directory": new_directory, "output": ""}
