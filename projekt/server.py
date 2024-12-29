import socket
import threading
from utils import *

BUFFER_SIZE = 102400  # 100 KB


class Connection:
    def __init__(self, name, client_socket, addr, server_on_remove):
        self.name = name
        self.client_socket = client_socket
        self.addr = addr
        self.server_on_remove = server_on_remove
        self.p = None
        self.g = None
        self.thread = threading.Thread(target=self.handle_client)

    def start(self):
        """Start the thread handling this connection."""
        self.thread.start()

    def close(self):
        """Close the connection and cleanup."""
        self.client_socket.close()
        self.print(f"Connection with {self.addr} closed.")
        self.server_on_remove(self)

    def print(self, mess):
        print(f"Client {self.name}:", mess)

    def handle_client(self):
        try:
            symmetric_key = self.perform_key_exchange(self.client_socket)
            self.communicate_with_client(self.client_socket, symmetric_key)
        except Exception as e:
            self.print(f"Error with client {self.addr}: {e}")
            self.print(f"Closing connection with {self.addr}")
            self.close()

    def perform_key_exchange(self, client_socket):
        self.print("Waiting for ClientHello")
        client_hello = receive_data(client_socket, 23)
        _, client_public_key, self.g, self.p = struct.unpack("!11sIII", client_hello)

        self.print(f"Received ClientHello with A={client_public_key}")

        # Server's private key and public key calculation
        server_private_key = generate_private_key()
        server_public_key = calculate_public_key(self.g, server_private_key, self.p)

        self.print(f"Sending ServerHello with B={server_public_key}")
        hello_message = struct.pack("!11sI", b"serverHello", server_public_key)
        client_socket.sendall(hello_message)

        shared_key = calculate_shared_key(client_public_key, server_private_key, self.p)
        symmetric_key = derive_symmetric_key(shared_key)

        self.print(f"Shared key K computed: {shared_key}, Symmetric key derived.")
        return symmetric_key

    def communicate_with_client(self, client_socket, symmetric_key):
        try:
            self.print("Waiting for messages from the client.")
            while True:
                message = read_string(client_socket)
                self.print(f"Received: {message}")
                response = "Hello from server!"
                send_string(client_socket, response)
        except ConnectionError:
            self.print("Lost connection to the client.")
        except Exception as e:
            self.print(f"Error: {e}")
        finally:
            self.print("Disconnected from client.")
            self.close()


class DiffieHellmanServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)

        print(f"Server listening on {self.host}:{self.port}...")

        self.next_client_id = 0
        self.connections = []

        self.running = True
        try:
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    print(f"\nConnection {self.next_client_id} established with {addr}")
                    connection = Connection(self.next_client_id,
                                            client_socket,
                                            addr,
                                            self.remove_connection)
                    self.connections.append(connection)
                    self.next_client_id += 1
                    connection.start()
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            print("\nShutting down server.")
            self.running = False
        finally:
            self.close_all_connections()
            self.server_socket.close()
            print("\nServer shut down.")

    def remove_connection(self, connection):
        """Remove a connection from the active list."""
        if connection in self.connections:
            self.connections.remove(connection)

    def close_all_connections(self):
        """Close all active connections."""
        for connection in self.connections:
            connection.close()
        self.connections = []

    def kill_connection(self, addr):
        """Kill a specific connection by address."""
        for connection in self.connections:
            if connection.addr == addr:
                connection.close()
                break


if __name__ == "__main__":
    port, host = process_args("server")

    server = DiffieHellmanServer(host, port)
    server.start()
