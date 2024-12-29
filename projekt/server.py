import socket
import threading
from utils import *

BUFFER_SIZE = 102400  # 100 KB


class Connection(threading.Thread):
    def __init__(self, client_id, client_socket, addr, remove_callback):
        super().__init__()
        self.client_id = client_id
        self.client_socket = client_socket
        self.addr = addr
        self.remove_callback = remove_callback
        self.p = None
        self.g = None
        self.running = True

    def run(self):
        """Handle the client logic."""
        try:
            symmetric_key = self.perform_key_exchange(self.client_socket)
            self.handle_client_message(self.client_socket, symmetric_key)
        except Exception as e:
            self.print(f"Error with client {self.client_id}: {e}")
        finally:
            self.stop()

    def stop(self):
        """Close the connection and clean up."""
        self.running = False
        self.client_socket.close()
        self.print(f"Connection with {self.addr} closed.")
        self.remove_callback(self)

    def print(self, mess):
        print(f"Client {self.client_id}:", mess)

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

    def handle_client_message(self, client_socket, symmetric_key):
        self.print("Waiting for messages from the client.")
        while self.running:
            message = read_string(client_socket)
            self.print(f"Received: {message}")
            response = "Hello from server!"
            send_string(client_socket, response)


class ConnectionsHandler(threading.Thread):
    def __init__(self, server_socket, timeout=1.0):
        super().__init__()
        self.server_socket = server_socket
        self.timeout = timeout
        self.stop_event = threading.Event()
        self.next_client_id = 0
        self.connections = []

    def run(self):
        """Accept connections in a loop until stopped."""
        self.server_socket.settimeout(self.timeout)
        try:
            while not self.stop_event.is_set():
                try:
                    client_socket, addr = self.server_socket.accept()
                    self.print(f"Connection {self.next_client_id} established with {addr}")
                    connection = Connection(self.next_client_id, client_socket, addr, self.remove_connection)
                    self.connections.append(connection)
                    self.next_client_id += 1
                    connection.start()
                except socket.timeout:
                    continue
        except Exception as e:
            self.print(f"encountered an error: {e}")
        finally:
            self.print("stopped.")

    def stop(self):
        """Stop accepting connections."""
        self.stop_event.set()

    def print(self, mess):
        print("ConnectionsHandler:", mess)

    def remove_connection(self, connection):
        """Remove a connection from the active list."""
        if connection in self.connections:
            self.connections.remove(connection)

    def close_all_connections(self):
        """Close all active connections."""
        for connection in self.connections:
            connection.stop()
            connection.join()
        self.connections = []

    def close_connection(self, id):
        """Close a specific connection by address."""
        for connection in self.connections:
            if connection.client_id == id:
                connection.stop()
                connection.join()
                break


class DiffieHellmanServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.connectionHandler = None

    def start(self):
        """Start the server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        print(f"Server listening on {self.host}:{self.port}...")

        self.connectionHandler = ConnectionsHandler(self.server_socket)
        self.connectionHandler.start()

        try:
            self.handle_input()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            self.stop()
        finally:
            print("\nServer shut down.")

    def stop(self):
        """Stop the server and clean up."""
        if self.connectionHandler:
            self.connectionHandler.stop()
            self.connectionHandler.join()
        self.connectionHandler.close_all_connections()
        if self.server_socket:
            self.server_socket.close()
        print("Server stopped.")

    def print_commands(self):
        print()
        print("Commands:")
        print("---------------------")
        print("ls")
        print("end <connection id>")
        print("---------------------")

    def handle_input(self):
        self.print_commands()
        while True:
            input_args = input("\nCommand: ").split(" ", 1)
            command = input_args[0]
            if command == "ls":
                self.print_connections()
            elif command == "end":
                if len(input_args) < 2:
                    print("end reqired id paramter!")
                else:
                    self.end_connection(input_args[1])
            else:
                print(f"command \"{command}\" not found")

    def print_connections(self):
        print()
        print("Connections:")
        print("---------------------")
        if len(self.connectionHandler.connections) > 0:
            for connection in self.connectionHandler.connections:
                print(f"Connection: {connection.client_id}")
        else:
            print("No active connection")
        print("---------------------")

    def end_connection(self, id):
        id = int(id)
        if id not in [c.client_id for c in self.connectionHandler.connections]:
            print(f"Connection with {id} id not found.")
            print(f"Use ls command to check existing connections")
            return
        self.connectionHandler.close_connection(id)
        print(f"Connection {id} closed")


if __name__ == "__main__":
    port, host = process_args("server")

    server = DiffieHellmanServer(host, port)
    server.start()
