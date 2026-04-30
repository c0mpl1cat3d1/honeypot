import time

from commands._transfer import basename_from_source, transfer_size_bytes, write_download


def _fmt_mmss(seconds):
    minutes = max(int(seconds) // 60, 0)
    secs = max(int(seconds) % 60, 0)
    return f"{minutes:02d}:{secs:02d}"


def _curl_progress_lines(total_bytes, steps=9):
    lines = ["  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current"]
    start = time.time()
    for step in range(1, steps + 1):
        pct = int(step * 100 / steps)
        received = int(total_bytes * pct / 100)
        elapsed = max(time.time() - start, 0.1)
        avg_speed = max(received / elapsed, 1024)
        remaining = max((total_bytes - received) / avg_speed, 0)
        line = (
            f"{pct:>3} {total_bytes // 1024:>7}k {pct:>3} {received // 1024:>7}k   0     0  "
            f"{int(avg_speed // 1024):>6}k      0 {_fmt_mmss(elapsed)} {_fmt_mmss(remaining)} {_fmt_mmss(elapsed)}"
        )
        lines.append(line)
        if step < steps:
            time.sleep(0.11 + (step % 3) * 0.05)
    return lines


def run(args, current_directory, context=None):
    if not args:
        return "curl: try 'curl --help' or 'curl --manual' for more information"
    if args[0] in ("-h", "--help"):
        return "Usage: curl [options...] <url>\n -o FILE  Write to file\n -O       Write output to a local file named like the remote file\n -T FILE  Transfer local FILE to destination"

    output = None
    remote_name = False
    upload = None
    urls = []
    index = 0

    while index < len(args):
        arg = args[index]
        if arg == "-o":
            if index + 1 >= len(args):
                return "curl: option -o requires parameter"
            output = args[index + 1]
            index += 2
            continue
        if arg == "-O":
            remote_name = True
            index += 1
            continue
        if arg == "-T":
            if index + 1 >= len(args):
                return "curl: option -T requires parameter"
            upload = args[index + 1]
            index += 2
            continue
        if arg.startswith("-"):
            index += 1
            continue
        urls.append(arg)
        index += 1

    if upload:
        destination = urls[0] if urls else "remote host"
        return f"curl: Uploaded '{upload}' to {destination}"

    if not urls:
        return "curl: no URL specified"

    url = urls[0]
    if output or remote_name:
        filename = output or basename_from_source(url)
        ok, error = write_download(current_directory, filename, url)
        if not ok:
            return f"curl: {error}"
        total_bytes = transfer_size_bytes(url, min_kb=120, max_kb=5200)
        return "\n".join(_curl_progress_lines(total_bytes))

    return "# Honeypot captured transfer attempt\n# Remote content was not fetched."
