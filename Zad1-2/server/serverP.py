import socket
import sys

MAX_BUF_SIZE = 512
TIMEOUT = 5
DEFAULT_PORT = 12345
DEFAULT_HOST = "0.0.0.0"


def process_args():
    if len(sys.argv) == 2:
        try:
            port = int(sys.argv[1])
        except ValueError as e:
            print(f"Invalid port number")
            sys.exit(1)
        return port, DEFAULT_HOST
    elif len(sys.argv) > 2:
        print("Too many arguments")
        sys.exit(1)
    return DEFAULT_PORT, DEFAULT_HOST


def handle_packet(data, expected_seq, client_address, socket: socket.socket):
    seq_num = data[0]

    if seq_num == expected_seq:
        print(f"Received packet with sequence {seq_num}")
        expected_seq = 1 - expected_seq
    else:
        print(f"Duplicate packet with sequence {seq_num}")

    socket.sendto(bytes([seq_num]), client_address)
    print(f"Sent ACK{seq_num}")

    return expected_seq


def start_server(host, port):
    print(f"Server listening on port {port}...")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind((host, port))

        expected_seq = 0
        while True:
            try:
                data, client_address = server_socket.recvfrom(MAX_BUF_SIZE)
                expected_seq = handle_packet(
                    data, expected_seq, client_address, server_socket
                )
            except Exception as e:
                print(f"Unexpected error: {e}")


if __name__ == "__main__":
    port, host = process_args()
    start_server(host, port)
