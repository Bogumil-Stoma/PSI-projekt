import socket
import time
import sys

TIMEOUT = 5
RETRY_LIMIT = 5
MAX_BUF_SIZE = 512
MESSAGE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_PORT = 12345
DEFAULT_HOST = "127.0.0.1"


def start_client(host, port):
    address = (host, port)
    seq_num = 0
    retries = 0

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        while retries < RETRY_LIMIT:
            if send_packet(client_socket, seq_num, MAX_BUF_SIZE, address):
                seq_num = 1 - seq_num
                retries = 0
            else:
                retries += 1
                print(f"Retry number: {retries}")

        if retries >= RETRY_LIMIT:
            print("Reached retry limit. Exiting.")


def send_packet(s: socket.socket, seq_num, max_payload_size, address):
    try:
        datagram = construct_datagram(seq_num, max_payload_size)
        s.sendto(datagram, address)
        print(f"Sent packet with sequence {seq_num}")

        ack, _ = s.recvfrom(MAX_BUF_SIZE)
        if ack[0] == seq_num:
            print(f"Received ACK{seq_num}")
            return True
        else:
            print(f"Invalid ACK, resend")
            return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def construct_datagram(seq_num, max_payload_size):
    return bytes([seq_num]) + message_to_bytes(max_payload_size - 1)


def message_to_bytes(length):
    return bytes([ord(MESSAGE[j % 26]) for j in range(length)])


def process_args():
    if len(sys.argv) == 2:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number")
            sys.exit(1)
        return port, DEFAULT_HOST
    elif len(sys.argv) == 3:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number")
            sys.exit(1)
        return port, sys.argv[2]
    elif len(sys.argv) > 3:
        print("Too many arguments")
        sys.exit(1)
    return DEFAULT_PORT, DEFAULT_HOST


if __name__ == "__main__":
    port, host = process_args()
    start_client(host, port)
