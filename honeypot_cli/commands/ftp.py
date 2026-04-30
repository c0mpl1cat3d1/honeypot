from commands._transfer import basename_from_source, write_download


def run(args, current_directory, context=None):
    if not args:
        return "ftp: missing host"
    if args[0] in ("-h", "--help"):
        return "usage: ftp host\nSupported batch commands: get, put"

    if args[0] in ("get", "recv"):
        if len(args) < 2:
            return "ftp: get: missing remote file"
        source = args[1]
        destination = args[2] if len(args) > 2 else basename_from_source(source, "download.bin")
        ok, error = write_download(current_directory, destination, source)
        if not ok:
            return f"ftp: {error}"
        return f"local: {destination} remote: {source}\n226 Transfer complete."

    if args[0] in ("put", "send"):
        if len(args) < 2:
            return "ftp: put: missing local file"
        return f"local: {args[1]} remote: {args[2] if len(args) > 2 else args[1]}\n226 Transfer complete."

    host = args[0]
    return "\n".join(
        [
            f"Connected to {host}.",
            "220 FTP server ready.",
            "Name: anonymous",
            "230 Login successful.",
            "ftp>",
        ]
    )
