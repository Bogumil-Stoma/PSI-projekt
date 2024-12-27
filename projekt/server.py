import socket
import sys
import struct
import threading

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


def send_string(sock, text):
    encoded_text = text.encode()
    text_size = len(encoded_text)
    packed_size = struct.pack("!I", text_size)
    sock.sendall(packed_size + encoded_text)

def handle_client(client_socket, addr):
    try:
        print(f"Handling client {addr}")
        while True:
            size_data = client_socket.recv(4)
            if not size_data:
                print(f"Client {addr} closed the connection.")
                break

            text_size = struct.unpack("!I", size_data)[0]
            text_data = client_socket.recv(text_size)
            if not text_data:
                print(f"Client {addr} sent incomplete data.")
                break

            text = text_data.decode()
            print(f"Received text: '{text}' from {addr}")

            response = "hello"
            send_string(client_socket, response)
            print(f"Sent response: '{response}' to {addr}")

    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        print(f"Closing connection with {addr}")
        client_socket.close()


def start_server(host, port):
    print(f"Server starting on {host}:{port}")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFFER_SIZE)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    try:
        while True:
            client_socket, addr = server_socket.accept()
            print(f"Connection established with {addr}")
            client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_thread.start()
    except KeyboardInterrupt:
        print("\nShutting down server.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    port, host = process_args()
    start_server(host, port)