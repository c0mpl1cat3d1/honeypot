import ipaddress


COMMON_SERVICES = [
    (22, "tcp", "open", "ssh"),
    (80, "tcp", "open", "http"),
    (443, "tcp", "closed", "https"),
]


def run(args, current_directory, context=None):
    if not args:
        return "\n".join(
            [
                "Nmap 7.80 ( https://nmap.org )",
                "Usage: nmap [Scan Type(s)] [Options] {target specification}",
            ]
        )

    if args[0] in ("-h", "--help"):
        return "\n".join(
            [
                "Nmap 7.80 ( https://nmap.org )",
                "Usage: nmap [options] target",
                "  -p PORTS       only scan specified ports",
                "  -sV            probe open ports to determine service/version info",
                "  -A             enable OS detection and version detection",
            ]
        )

    options, targets, error = parse_args(args)
    if error:
        return error
    if not targets:
        return "nmap: No targets specified."

    reports = [scan_target(target, options) for target in targets[:4]]
    return "\n\n".join(reports)


def parse_args(args):
    options = {"ports": None, "version": False, "aggressive": False}
    targets = []
    index = 0

    while index < len(args):
        arg = args[index]

        if arg == "--":
            targets.extend(args[index + 1 :])
            break

        if arg == "-p":
            if index + 1 >= len(args):
                return options, targets, "nmap: option '-p' requires an argument"
            ports, error = parse_ports(args[index + 1])
            if error:
                return options, targets, error
            options["ports"] = ports
            index += 2
            continue

        if arg.startswith("-p") and len(arg) > 2:
            ports, error = parse_ports(arg[2:])
            if error:
                return options, targets, error
            options["ports"] = ports
            index += 1
            continue

        if arg == "-sV":
            options["version"] = True
            index += 1
            continue

        if arg == "-A":
            options["aggressive"] = True
            options["version"] = True
            index += 1
            continue

        if arg.startswith("-"):
            return options, targets, f"nmap: unrecognized option '{arg}'"

        targets.append(arg)
        index += 1

    return options, targets, None


def parse_ports(value):
    ports = []

    for part in value.split(","):
        if "-" in part:
            start, end = part.split("-", 1)
            if not start.isdigit() or not end.isdigit():
                return ports, f"nmap: invalid port range '{part}'"
            start_port = int(start)
            end_port = int(end)
            if start_port > end_port:
                return ports, f"nmap: invalid port range '{part}'"
            ports.extend(range(start_port, min(end_port, start_port + 20) + 1))
            continue

        if not part.isdigit():
            return ports, f"nmap: invalid port '{part}'"
        ports.append(int(part))

    ports = [port for port in ports if 1 <= port <= 65535]
    if not ports:
        return ports, "nmap: No valid ports specified"

    return sorted(dict.fromkeys(ports)), None


def scan_target(target, options):
    address = resolve_target(target)
    services = selected_services(options["ports"])

    lines = [
        "Starting Nmap 7.80 ( https://nmap.org )",
        f"Nmap scan report for {target} ({address})",
        "Host is up (0.0042s latency).",
        "Not shown: 997 filtered ports",
        "PORT     STATE  SERVICE" + (" VERSION" if options["version"] else ""),
    ]

    for port, protocol, state, service in services:
        line = f"{port}/{protocol:<5} {state:<6} {service}"
        if options["version"] and state == "open":
            line += version_for(service)
        lines.append(line)

    if options["aggressive"]:
        lines.extend(
            [
                "Device type: general purpose",
                "Running: Linux 5.X",
                "OS CPE: cpe:/o:linux:linux_kernel:5",
            ]
        )

    lines.append("Nmap done: 1 IP address (1 host up) scanned in 0.38 seconds")
    return "\n".join(lines)


def selected_services(ports):
    if ports is None:
        return COMMON_SERVICES

    known = {port: (port, protocol, state, service) for port, protocol, state, service in COMMON_SERVICES}
    return [known.get(port, (port, "tcp", "closed", "unknown")) for port in ports[:12]]


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


def version_for(service):
    versions = {
        "ssh": " OpenSSH 8.2p1 Ubuntu 4ubuntu0.9",
        "http": " Apache httpd 2.4.41",
    }
    return versions.get(service, "")
