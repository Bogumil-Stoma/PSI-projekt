import socket
import sys

MAX_BUF_SIZE = 160000


def main():
    print(f"Server listening on port {PORT}...")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, PORT))

        while True:
            data, address = s.recvfrom(MAX_BUF_SIZE)
            length = (data[0] << 8) | data[1]
            if length != len(data):
                print("Received datagram length mismatch")
            else:
                print(f"Received datagram of length {len(data)}")

            response = b"OK"
            s.sendto(response, address)


def process_args():
    port = 12345
    host = '0.0.0.0'
    arg_count = len(sys.argv)

    if arg_count == 2:
        port = int(sys.argv[1])
    elif arg_count > 2:
        print("Too many arguments provided. Exiting.")
        sys.exit(1)
    return port, host


PORT, HOST = process_args()

if __name__ == "__main__":
    main()
