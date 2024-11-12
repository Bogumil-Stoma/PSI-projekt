import socket

MAX_BUF_SIZE = 160000
BYTES_ITERATION_SIZE = 1000
ITERATIONS = 100
MESSAGE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        for i in range(1, ITERATIONS):
            length = i * BYTES_ITERATION_SIZE
            try:
                send_datagram(s, length)
            except Exception as e:
                print(f"Error sending datagram: {e}")
                break

        start_length = length
        for length in range(start_length - BYTES_ITERATION_SIZE, start_length):
            try:
                send_datagram(s, length)
            except Exception as e:
                print(f"Error sending datagram: {e}")
                break

import sys

def process_args():
    port = 12345
    host = "172.21.35.2"
    arg_count = len(sys.argv)

    if arg_count == 2:
        port = int(sys.argv[1])
    elif arg_count == 3:
        port = int(sys.argv[1])
        host = sys.argv[2]
    elif arg_count > 3:
        print("Too many arguments provided. Exiting.")
        sys.exit(1)
    return port, host

PORT, HOST = process_args()

def send_datagram(s, length):
    data = length_to_bytes(length) + message_to_bytes(length-2)
    bytes_sent = s.sendto(data, (HOST, PORT))
    check_data(bytes_sent, data)
    
    response, _ = s.recvfrom(MAX_BUF_SIZE)
    print(f"Received from server: {response.decode()}")


def check_data(bytes_sent, data):
    if bytes_sent != len(data):
        print("Error: Not all data sent.")
    else:
        print(f"Sent {bytes_sent} bytes.")

def length_to_bytes(length):
    return length.to_bytes(2, byteorder='big')

def message_to_bytes(length):
    return bytes([ord(MESSAGE[j % 26]) for j in range(length)])

if __name__ == "__main__":
    main()
