from commands._transfer import basename_from_source, is_remote_path, remote_host, write_download


def run(args, current_directory, context=None):
    if not args:
        return "usage: sftp [-P port] [user@]host"
    if args[0] in ("-h", "--help"):
        return "usage: sftp [-P port] [user@]host\nSupported batch commands: get, put"

    if args[0] == "get":
        if len(args) < 2:
            return "File not found."
        source = args[1]
        destination = args[2] if len(args) > 2 else basename_from_source(source, "download.bin")
        ok, error = write_download(current_directory, destination, source)
        if not ok:
            return f"sftp: {error}"
        return f"Fetching {source} to {destination}\n{destination}                                      100%  128     1.0KB/s   00:00"

    if args[0] == "put":
        if len(args) < 2:
            return "File not found."
        return f"Uploading {args[1]} to {args[2] if len(args) > 2 else args[1]}\n{args[1]}                                      100%  128     1.0KB/s   00:00"

    host = next((arg for arg in args if not arg.startswith("-")), args[-1])
    if is_remote_path(host):
        host = remote_host(host)
    return f"Connected to {host}.\nsftp>"
