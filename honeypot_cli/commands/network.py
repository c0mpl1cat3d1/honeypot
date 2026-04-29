def run(args, current_directory):
    if args and args[0] in ("-h", "--help", "help"):
        return "Usage: network [status|interfaces|routes|dns]"

    action = args[0] if args else "status"

    if action == "status":
        return "\n".join(
            [
                "NetworkManager is running",
                "eth0: connected to Wired connection 1",
                "lo: unmanaged",
                "default route: 10.0.2.2 via eth0",
            ]
        )

    if action in ("interfaces", "ifaces"):
        return "\n".join(
            [
                "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500",
                "        inet 10.0.2.15  netmask 255.255.255.0  broadcast 10.0.2.255",
                "        ether 08:00:27:12:34:56  txqueuelen 1000",
                "lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536",
                "        inet 127.0.0.1  netmask 255.0.0.0",
            ]
        )

    if action == "routes":
        return "\n".join(
            [
                "Kernel IP routing table",
                "Destination     Gateway         Genmask         Flags Iface",
                "0.0.0.0         10.0.2.2        0.0.0.0         UG    eth0",
                "10.0.2.0        0.0.0.0         255.255.255.0   U     eth0",
            ]
        )

    if action == "dns":
        return "\n".join(["nameserver 8.8.8.8", "nameserver 1.1.1.1"])

    return f"network: unknown action '{action}'"
