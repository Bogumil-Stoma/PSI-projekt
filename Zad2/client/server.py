import socket
import sys
import struct

DEFAULT_PORT = 12345
DEFAULT_HOST = "0.0.0.0"
BUFFER_SIZE = 102400  # 100 kB

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

def handle_client(client_socket):
    data = client_socket.recv(BUFFER_SIZE)
    if not data:
        print("No data received.")
        return

    print(f"Received {len(data)} bytes of binary data.")

    offset = 0
    while offset < len(data):

        # read text1
        if offset + 4 > len(data):
           break

        text1_size = struct.unpack("!I", data[offset:offset + 4])[0]
        offset += 4

        if offset + text1_size > len(data):
           break

        text1 = data[offset:offset + text1_size].decode()
        offset += text1_size

        # read text2
        if offset + 4 > len(data):
           break

        text2_size = struct.unpack("!I", data[offset:offset + 4])[0]
        offset += 4

        if offset + text2_size > len(data):
           break
        text2 = data[offset:offset + text2_size].decode()
        offset += text2_size

        print(f"Node received: text1='{text1}' s={text1_size}, text2='{text2}' s={text2_size}")


def start_server(host, port):
    print(f"Server starting on {host}:{port}")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFFER_SIZE)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection established with {addr}")
        handle_client(client_socket)
        client_socket.close()

if __name__ == "__main__":
    port, host = process_args()
    start_server(host, port)
