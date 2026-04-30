from commands._transfer import basename_from_source, write_download


def run(args, current_directory, context=None):
    if not args:
        return "tftp: missing host"
    if args[0] in ("-h", "--help"):
        return "usage: tftp host [-c get FILE] [-c put FILE]"

    host = args[0]
    if "-c" not in args:
        return f"Connected to {host}.\ntftp>"

    command_index = args.index("-c")
    if command_index + 2 >= len(args):
        return "tftp: option -c requires command and file"

    action = args[command_index + 1]
    filename = args[command_index + 2]

    if action == "get":
        destination = basename_from_source(filename, "download.bin")
        ok, error = write_download(current_directory, destination, f"tftp://{host}/{filename}")
        if not ok:
            return f"tftp: {error}"
        return f"Received {destination} from {host}"

    if action == "put":
        return f"Sent {filename} to {host}"

    return f"tftp: unknown command '{action}'"
