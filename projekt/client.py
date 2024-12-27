import socket
import time
from utils import *


class DiffieHellmanClient:
    def __init__(self, host, port, g, p):
        self.host = host
        self.port = port
        self.g = g
        self.p = p
        self.client_socket = None

    def perform_key_exchange(self, private_key, public_key):
        hello_message = struct.pack("!11sIII", b"ClientHello", public_key, self.p,
                                    self.g)
        self.client_socket.sendall(hello_message)
        print(f"Sent ClientHello with A={public_key}, p={self.p}, g={self.g}")

        server_hello = receive_data(self.client_socket, 15)  # 11 + 16 + 16
        _, server_public_key = struct.unpack("!11sI", server_hello)

        print(f"Received ServerHello with B={server_public_key}")

        shared_key = calculate_shared_key(server_public_key, private_key, self.p)
        symmetric_key = derive_symmetric_key(shared_key)

        print(f"Shared key K computed: {shared_key}, Symmetric key derived.")
        return symmetric_key

    def communicate_with_server(self, symmetric_key):
        try:
            print("Connected to the server.")

            while True:
                message = "hello"

                print(f"Sending: {message}")

                send_string(self.client_socket, message)
                response = read_string(self.client_socket)

                print(f"Received: {response}")

                time.sleep(1)
        except ConnectionError:
            print("Lost connection to the server.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            print("Disconnected from server.")

    def start(self):
        private_key = generate_private_key()
        public_key = calculate_public_key(self.g, private_key, self.p)

        print(f"Connecting to server at {self.host}:{self.port}...")

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(10)
        self.client_socket.connect((self.host, self.port))

        try:
            symmetric_key = self.perform_key_exchange(private_key, public_key)
            self.communicate_with_server(symmetric_key)
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            self.client_socket.close()


if __name__ == "__main__":
    port, host = process_args("client")
    client = DiffieHellmanClient(host, port, 5, 23)
    client.start()