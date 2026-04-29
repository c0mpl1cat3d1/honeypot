def run(args, current_directory):
    if not args or args[0] in ("-h", "--help"):
        return "\n".join(
            [
                "OpenBSD netcat (Debian patchlevel 1.206-1ubuntu1)",
                "usage: nc [-46CDdFhklNnrStUuvZz] [-I length] [-i interval]",
                "          [-M ttl] [-m minttl] [-O length] [-P proxy_username]",
                "          [-p source_port] [-q seconds] [-s sourceaddr] [-T keyword]",
                "          [-V rtable] [-W recvlimit] [-w timeout] [-X proxy_protocol]",
                "          [-x proxy_address[:port]] [destination] [port]",
            ]
        )

    if "-l" in args or "-lp" in args:
        port = _value_after(args, "-p") or _port_after_listen(args) or "31337"
        return f"listening on [any] {port} ..."

    destination = None
    port = None
    for item in args:
        if item.startswith("-"):
            continue
        if destination is None:
            destination = item
        elif port is None:
            port = item
            break

    if destination and port:
        if "-z" in args or "-vz" in args or "-zv" in args:
            return f"Connection to {destination} {port} port [tcp/*] succeeded!"
        return f"Trying {destination} {port}...\nConnected to {destination}.\nEscape character is '^]'."

    return "nc: missing destination or port"


def _value_after(args, option):
    try:
        index = args.index(option)
    except ValueError:
        return None

    if index + 1 < len(args):
        return args[index + 1]
    return None


def _port_after_listen(args):
    for index, item in enumerate(args):
        if item in ("-l", "-lp") and index + 1 < len(args):
            candidate = args[index + 1]
            if not candidate.startswith("-"):
                return candidate
    return None
