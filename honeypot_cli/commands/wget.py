from commands._transfer import (
    basename_from_source,
    simulate_wget_progress,
    transfer_size_bytes,
    write_download,
)


def run(args, current_directory, context=None):
    if not args:
        return "wget: missing URL"
    if args[0] in ("-h", "--help"):
        return "Usage: wget [OPTION]... [URL]...\n  -O FILE    write documents to FILE"

    output = None
    urls = []
    index = 0

    while index < len(args):
        arg = args[index]
        if arg in ("-O", "--output-document"):
            if index + 1 >= len(args):
                return "wget: option requires an argument -- 'O'"
            output = args[index + 1]
            index += 2
            continue
        if arg.startswith("-O") and len(arg) > 2:
            output = arg[2:]
            index += 1
            continue
        if arg.startswith("-"):
            index += 1
            continue
        urls.append(arg)
        index += 1

    if not urls:
        return "wget: missing URL"

    lines = []
    for url in urls[:4]:
        filename = output or basename_from_source(url)
        ok, error = write_download(current_directory, filename, url)
        if not ok:
            lines.append(f"wget: {error}")
            continue
        total_bytes = transfer_size_bytes(url, min_kb=180, max_kb=5600)

        lines.extend(
            [
                f"--2026-04-30--  {url}",
                "Resolving host... connected.",
                "HTTP request sent, awaiting response... 200 OK",
                f"Saving to: '{filename}'",
                "",
            ]
        )
        lines.extend(simulate_wget_progress(total_bytes))
        lines.extend(["", f"'{filename}' saved [{total_bytes}/{total_bytes}]"])

    return "\n".join(lines)
