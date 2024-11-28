import socket
import sys
import struct

MAX_BUF_SIZE = 1024
DEFAULT_PORT = 12345
DEFAULT_HOST = "0.0.0.0"

def process_args():
    if len(sys.argv) == 2:
        try:
            port = int(sys.argv[1])
        except ValueError as e:
            print(f"Invalid port number: {e}")
            sys.exit(1)
        return port, DEFAULT_HOST
    elif len(sys.argv) > 2:
        print("Too many arguments")
        sys.exit(1)
    return DEFAULT_PORT, DEFAULT_HOST

def receive_data(conn):
    while True:
        text1_len_data = conn.recv(4)
        if not text1_len_data:
            print("End of data")
            break

        text1_len = struct.unpack("!I", text1_len_data)[0] # ! - bigendian, I - int

        if text1_len == 0:
            break

        text1 = conn.recv(text1_len).decode()

        text2_len_data = conn.recv(4)
        text2_len = struct.unpack("!I", text2_len_data)[0]

        text2 = conn.recv(text2_len).decode()

        print(f"Node received: text1='{text1}' s={text1_len}, text2='{text2}' s={text2_len}")


def start_server(host, port):
    print(f"Server starting on {host}:{port}")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    conn, addr = server_socket.accept()
    print(f"Connection established with {addr}")

    receive_data(conn)
    conn.close()
    print("Connection closed.")

if __name__ == "__main__":
    port, host = process_args()
    start_server(host, port)
