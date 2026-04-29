def run(args, current_directory):
    filename = args[0] if args else None

    if filename in ("-h", "--help"):
        return "\n".join(
            [
                "VIM - Vi IMproved 8.1",
                "usage: vim [arguments] [file ..]",
                "   vim file        edit file",
                "   vim -R file     readonly mode",
            ]
        )

    if filename:
        mode = "readonly" if "-R" in args else "editing"
        return f'Vim: {mode} "{filename}"\nPress ENTER or type command to continue'

    return "Vim: Warning: Input is not from a terminal"
