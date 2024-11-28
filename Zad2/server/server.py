import socket
import sys
import struct

DEFAULT_PORT = 12345
DEFAULT_HOST = "0.0.0.0"
BUFFER_SIZE = 102400  # 100 KB


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


def is_data_accessible(data, offset, num_of_bytes):
    return offset + num_of_bytes <= len(data)


def read_string(data, offset):
    if not is_data_accessible(data, offset, 4):
        return None, 0, offset

    text_size = struct.unpack("!I", data[offset:offset + 4])[0]
    offset += 4

    if not is_data_accessible(data, offset, text_size):
        return None, 0, offset

    text = data[offset:offset + text_size].decode()
    offset += text_size

    return text, text_size, offset


def handle_client(client_socket):
    data = client_socket.recv(BUFFER_SIZE)
    if not data:
        print("No data received.")
        return

    print(f"Received {len(data)} bytes of binary data.")

    offset = 0
    while offset < len(data):
        # read text1
        text1, text1_size, offset = read_string(data, offset)
        if text1 is None:
            break

        # read text2
        text2, text2_size, offset = read_string(data, offset)
        if text2 is None:
            break

        print(f"Node received: text1='{text1}' s={text1_size}, \
              text2='{text2}', s={text2_size}")


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
