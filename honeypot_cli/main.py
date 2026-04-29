from core.ssh_server import start_ssh_server

HOST = "0.0.0.0"
PORT = 2222


if __name__ == "__main__":
    start_ssh_server(host=HOST, port=PORT)