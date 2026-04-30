import posixpath
import time
import hashlib
from urllib.parse import urlparse

from core.filesystem import FileSystem


def basename_from_source(source, default_name="index.html"):
    parsed = urlparse(source)
    path = parsed.path if parsed.scheme else source
    name = posixpath.basename(path.rstrip("/"))
    return name or default_name


def safe_payload(source):
    return "\n".join(
        [
            "# Honeypot captured transfer attempt",
            f"# Source: {source}",
            "# Network access disabled; original remote content was not fetched.",
            "",
        ]
    )


def write_download(current_directory, output_path, source):
    fs = FileSystem()
    ok, error = fs.write_file(current_directory, output_path, safe_payload(source))
    return ok, error


def is_remote_path(value):
    return "://" in value or (":" in value and not value.startswith("/"))


def remote_host(value):
    parsed = urlparse(value)
    if parsed.scheme:
        return parsed.netloc or parsed.path
    return value.split(":", 1)[0]


def transfer_size_bytes(seed_text, min_kb=256, max_kb=8192):
    digest = hashlib.sha1(seed_text.encode("utf-8")).digest()
    span = max(max_kb - min_kb, 1)
    value_kb = min_kb + (int.from_bytes(digest[:4], "big") % (span + 1))
    return value_kb * 1024


def human_size(num_bytes):
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f}M"
    return f"{num_bytes / 1024:.0f}K"


def progress_bar(percent, width=26):
    filled = int((percent / 100) * width)
    if filled >= width:
        return "=" * width
    return ("=" * filled) + ">" + (" " * (width - filled - 1))


def simulate_wget_progress(total_bytes, steps=10):
    lines = []
    start = time.time()
    for step in range(1, steps + 1):
        percent = int(step * 100 / steps)
        transferred = int(total_bytes * percent / 100)
        elapsed = max(time.time() - start, 0.12)
        rate_bps = max(transferred / elapsed, 1024)
        eta = max(int((total_bytes - transferred) / rate_bps), 0)
        lines.append(
            f"{percent:>4}%[{progress_bar(percent)}] "
            f"{human_size(transferred):>6}  {rate_bps / 1024:>6.0f}KB/s    eta {eta:>2d}s"
        )
        if step < steps:
            time.sleep(0.12 + (step % 3) * 0.05)
    return lines


def simulate_scp_progress(filename, total_bytes, steps=8):
    start = time.time()
    line = ""
    for step in range(1, steps + 1):
        percent = int(step * 100 / steps)
        transferred = int(total_bytes * percent / 100)
        elapsed = max(time.time() - start, 0.12)
        rate = max((transferred / 1024) / elapsed, 1.0)
        eta = max(int((total_bytes - transferred) / 1024 / max(rate, 1.0)), 0)
        line = (
            f"{filename:<32} {percent:>3}%  "
            f"{transferred / 1024:>5.0f}KB  {rate:>6.1f}KB/s   00:{eta:02d}"
        )
        if step < steps:
            time.sleep(0.14 + (step % 2) * 0.06)
    return line
