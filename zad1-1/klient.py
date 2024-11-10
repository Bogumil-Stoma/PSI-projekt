import socket
import time

MAX_BUF_SIZE = 160000
HOST = '127.0.0.1'
PORT = 12345
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

    time.sleep(5)

def send_datagram(s, length):
    data = length_to_bytes(length) + message_to_bytes(length)
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
