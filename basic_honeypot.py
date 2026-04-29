import socket
import threading
import time

HOST = "0.0.0.0"
PORT = 2222
LOG_FILE = "honeypot.log"

def log(message):
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")
    print(message)

def safe_decode(data):
    try:
        return data.decode("utf-8")
    except:
        return str(data)

def handle_client(client, addr):
    ip, port = addr
    log(f"[CONNECTION] {ip}:{port}")

    try:
        # Send fake SSH banner
        banner = b"SSH-2.0-OpenSSH_7.4\r\n"
        client.send(banner)

        time.sleep(0.5)

        # Receive first packet (could be binary SSH handshake)
        data = client.recv(1024)

        if not data:
            client.close()
            return

        # Log raw incoming data
        log(f"[RAW] {ip}: {data}")

        # Detect binary SSH handshake
        if b"\x00" in data or b"\xff" in data:
            log(f"[BINARY DETECTED] Likely real SSH client from {ip}")
            client.close()
            return

        # Otherwise treat as text interaction
        decoded = safe_decode(data).strip()

        # Ask for login
        client.send(b"login: ")
        username = safe_decode(client.recv(1024)).strip()

        client.send(b"Password: ")
        password = safe_decode(client.recv(1024)).strip()

        log(f"[LOGIN] {ip} | Username: {username} | Password: {password}")

        time.sleep(1)
        client.send(b"Access denied\r\n")

    except Exception as e:
        log(f"[ERROR] {ip}: {str(e)}")

    finally:
        client.close()
        log(f"[DISCONNECTED] {ip}")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(100)

    print(f"[STARTED] Fake SSH honeypot running on port {PORT}")

    while True:
        client, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client, addr))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    start_server()
  