import socket
import threading
from utils import *
import time

BUFFER_SIZE = 102400  # 100 KB


class DiffieHellmanServer:
    def __init__(self, host, port):
        self.p = None
        self.g = None
        self.host = host
        self.port = port
        self.server_socket = None

    def handle_client(self, client_socket, addr):
        try:
            symmetric_key = self.perform_key_exchange(client_socket)
            self.communicate_with_client(client_socket, symmetric_key)
        except Exception as e:
            print(f"Error with client {addr}: {e}")
        finally:
            print(f"Closing connection with {addr}")
            client_socket.close()

    def perform_key_exchange(self, client_socket):
        client_hello = receive_data(client_socket, 23)
        _, client_public_key, self.g, self.p = struct.unpack("!11sIII", client_hello)

        print(f"Received ClientHello with A={client_public_key}")

        # Server's private key and public key calculation
        server_private_key = generate_private_key()
        server_public_key = calculate_public_key(self.g, server_private_key, self.p)

        print(f"Sending ServerHello with B={server_public_key}")
        hello_message = struct.pack("!11sI", b"serverHello", server_public_key)
        client_socket.sendall(hello_message)

        shared_key = calculate_shared_key(client_public_key, server_private_key, self.p)
        symmetric_key = derive_symmetric_key(shared_key)

        print(f"Shared key K computed: {shared_key}, Symmetric key derived.")
        return symmetric_key

    def communicate_with_client(self, client_socket, symmetric_key):
        try:
            print("Waiting for messages from the client.")
            while True:
                message = read_string(client_socket)
                print(f"Received: {message}")
                response = "Hello from server!"
                send_string(client_socket, response)
                time.sleep(1)
        except ConnectionError:
            print("Lost connection to the client.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            print("Disconnected from client.")

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        print(f"Server listening on {self.host}:{self.port}...")

        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                print(f"Connection established with {addr}")
                client_thread = threading.Thread(target=self.handle_client,
                                                 args=(client_socket, addr))
                client_thread.start()
        except KeyboardInterrupt:
            print("\nShutting down server.")
        finally:
            self.server_socket.close()

if __name__ == "__main__":
    port, host = process_args("server")

    server = DiffieHellmanServer(host, port)
    server.start()