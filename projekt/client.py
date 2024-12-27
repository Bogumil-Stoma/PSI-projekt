import socket
import struct
import sys
import time

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 12345

def send_string(sock, text):
    encoded_text = text.encode()
    text_size = len(encoded_text)
    packed_size = struct.pack("!I", text_size)
    sock.sendall(packed_size + encoded_text)

def read_string(sock):
    size_data = sock.recv(4)
    if not size_data:
        return None
    text_size = struct.unpack("!I", size_data)[0]
    text_data = sock.recv(text_size)
    return text_data.decode()

def start_client(host, port):
    print(f"Connecting to server at {host}:{port}...")
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(10)
    try:
        client_socket.connect((host, port))
        print(f"Connected to server.")

        while True:
            message = "hello"
            print(f"Sending: {message}")
            send_string(client_socket, message)

            response = read_string(client_socket)
            print(f"Received: {response}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()
        print("Disconnected from server.")

if __name__ == "__main__":
    host = DEFAULT_HOST
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])


    start_client(host, port)
