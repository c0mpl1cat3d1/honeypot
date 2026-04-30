import ipaddress


def run(args, current_directory, context=None):
    if not args:
        return "ping: usage error: Destination address required"

    if args[0] in ("-h", "--help"):
        return "\n".join(
            [
                "Usage: ping [OPTION...] HOST",
                "Send ICMP ECHO_REQUEST packets to network hosts.",
                "  -c COUNT      stop after sending COUNT packets",
                "  -i INTERVAL   seconds between sending each packet",
            ]
        )

    count, target, error = parse_args(args)
    if error:
        return error
    if target is None:
        return "ping: usage error: Destination address required"

    ip = resolve_target(target)
    loss = 100 if target.endswith(".0") or target.endswith(".255") else 0
    received = 0 if loss else count

    lines = [f"PING {target} ({ip}) 56(84) bytes of data."]

    if not loss:
        for sequence in range(1, count + 1):
            time_ms = 0.183 + sequence * 0.041
            lines.append(f"64 bytes from {ip}: icmp_seq={sequence} ttl=64 time={time_ms:.3f} ms")

    lines.extend(
        [
            "",
            f"--- {target} ping statistics ---",
            f"{count} packets transmitted, {received} received, {loss}% packet loss, time {max(count - 1, 0) * 1000}ms",
        ]
    )

    if received:
        lines.append("rtt min/avg/max/mdev = 0.224/0.268/0.306/0.031 ms")

    return "\n".join(lines)


def parse_args(args):
    count = 4
    target = None
    index = 0

    while index < len(args):
        arg = args[index]

        if arg == "--":
            if index + 1 < len(args):
                target = args[index + 1]
            break

        if arg == "-c":
            if index + 1 >= len(args):
                return count, target, "ping: option requires an argument -- 'c'"
            try:
                count = max(1, min(int(args[index + 1]), 10))
            except ValueError:
                return count, target, f"ping: invalid argument: '{args[index + 1]}'"
            index += 2
            continue

        if arg == "-i":
            if index + 1 >= len(args):
                return count, target, "ping: option requires an argument -- 'i'"
            index += 2
            continue

        if arg.startswith("-"):
            return count, target, f"ping: invalid option -- '{arg[1:2]}'"

        target = arg
        index += 1

    return count, target, None


def resolve_target(target):
    try:
        return str(ipaddress.ip_address(target))
    except ValueError:
        pass

    known_hosts = {
        "localhost": "127.0.0.1",
        "raspberrypi": "10.0.2.15",
        "raspberrypi.local": "10.0.2.15",
        "gateway": "10.0.2.2",
    }
    return known_hosts.get(target, "93.184.216.34")
