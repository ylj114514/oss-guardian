import socket
import threading
import time
import subprocess


def _start_server(port_holder):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port_holder.append(server.getsockname()[1])
    conn, _ = server.accept()
    conn.sendall(b"hi")
    conn.close()
    server.close()


def main():
    port_holder = []
    t = threading.Thread(target=_start_server, args=(port_holder,), daemon=True)
    t.start()
    while not port_holder:
        time.sleep(0.05)

    client = socket.create_connection(("127.0.0.1", port_holder[0]))
    client.recv(2)
    client.close()

    with open("demo_output.txt", "w", encoding="utf-8") as f:
        f.write("hello")

    eval("1+1")
    subprocess.run(["cmd", "/c", "echo", "dynamic-demo"], check=False)


if __name__ == "__main__":
    main()
