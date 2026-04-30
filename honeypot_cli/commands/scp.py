from commands._transfer import (
    basename_from_source,
    is_remote_path,
    remote_host,
    simulate_scp_progress,
    transfer_size_bytes,
    write_download,
)


def run(args, current_directory, context=None):
    if not args or args[0] in ("-h", "--help"):
        return "usage: scp [-r] [-P port] [[user@]host1:]file1 ... [[user@]host2:]file2"

    operands = [arg for arg in args if not arg.startswith("-")]
    if len(operands) < 2:
        return "scp: missing source or destination"

    source = operands[-2]
    destination = operands[-1]

    if is_remote_path(source) and not is_remote_path(destination):
        filename = destination
        if destination in (".", "./") or destination.endswith("/"):
            filename = basename_from_source(source, "download.bin")
        ok, error = write_download(current_directory, filename, source)
        if not ok:
            return f"scp: {error}"
        name = basename_from_source(source, filename)
        total_bytes = transfer_size_bytes(source, min_kb=64, max_kb=4096)
        return simulate_scp_progress(name, total_bytes)

    if not is_remote_path(source) and is_remote_path(destination):
        total_bytes = transfer_size_bytes(source + destination, min_kb=64, max_kb=4096)
        progress = simulate_scp_progress(source, total_bytes)
        return f"{progress}\nsent to {remote_host(destination)}"

    return "scp: Connection closed"
