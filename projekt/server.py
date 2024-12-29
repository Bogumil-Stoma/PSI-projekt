import socket
import threading
import struct
from utils import *


class Connection(threading.Thread):
    def __init__(self, client_id, client_socket, addr, remove_callback, printer):
        super().__init__()
        self.client_id = client_id
        self.client_socket = client_socket
        self.addr = addr
        self.remove_callback = remove_callback
        self.printer = printer
        self.p = None
        self.g = None
        self.stop_event = threading.Event()

    def run(self):
        """Handle the client logic."""
        try:
            self.symmetric_key = self.perform_key_exchange(self.client_socket)
            self.handle_client_message(self.client_socket)
        except Exception as e:
            self.print(f"Error with client {self.client_id}: {e}")
        finally:
            self.stop()

    def stop(self):
        """Close the connection and clean up."""
        self.client_socket.close()
        self.print(f"Connection with {self.addr} closed.")
        self.remove_callback(self)
        self.stop_event.set()

    def print(self, mess):
        self.printer(f"Client {self.client_id}: {mess}")

    def perform_key_exchange(self, client_socket):
        self.print("Waiting for ClientHello")
        client_hello = receive_data(client_socket, 23)
        _, client_public_key, self.p, self.g = struct.unpack("!11sIII", client_hello)

        self.print(f"Received ClientHello with A={client_public_key} p={self.p} g={self.g}")

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

    def handle_client_message(self, client_socket):
        self.print("Waiting for messages from the client.")
        while not self.stop_event.is_set():

            # Read data
            message_size_data = receive_data(self.client_socket, 4)
            message_size = struct.unpack("!I", message_size_data)[0]
            iv = receive_data(self.client_socket, 16)
            ciphertext = receive_data(self.client_socket, message_size)
            mac = receive_data(self.client_socket, 32)

            calculated_mac = calculate_hmac(ciphertext, self.symmetric_key)
            if mac != calculated_mac:
                self.print("Authentication failed")
                self.print("get", mac, "\ncalculated", calculated_mac)
                # todo: disconnect client
                return

            decrypted_message = aes_cbc_decrypt(iv, ciphertext, self.symmetric_key)
            self.print(f"Recived: {decrypted_message}")

            # todo: replace it by ennd connection message
            response = "Hello from server!"
            send_string(client_socket, response)


class ConnectionsHandler(threading.Thread):
    def __init__(self, server_socket, printer, timeout=1.0):
        super().__init__()
        self.server_socket = server_socket
        self.printer = printer
        self.timeout = timeout
        self.lock = threading.Lock()
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
                    connection = Connection(self.next_client_id,
                                            client_socket,
                                            addr,
                                            self.remove_connection,
                                            self.printer)
                    self.connections.append(connection)
                    self.next_client_id += 1
                    connection.start()
                except socket.timeout:
                    continue
        except Exception as e:
            self.print(f"encountered an error: {e}")
        finally:
            self.print("Stopped")

    def stop(self):
        """Stop accepting connections."""
        self.stop_event.set()
        self.stop_event.wait()
        self.join()
        self.close_all_connections()

    def print(self, mess):
        self.printer(f"ConnectionsHandler: {mess}")

    def remove_connection(self, connection):
        """Remove a connection from the active list."""
        if self.stop_event.is_set():
            return
        with self.lock:
            if connection in self.connections:
                self.connections.remove(connection)

    def close_all_connections(self):
        """Close all active connections."""
        self.print("Closing all connections")
        with self.lock:
            for connection in self.connections:
                connection.stop()
                connection.join()
                connection.stop_event.wait()
            self.connections = []

    def close_connection(self, id):
        """Close a specific connection by address."""
        with self.lock:
            for connection in self.connections:
                if connection.client_id == id:
                    connection.stop()
                    break


class DiffieHellmanServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.connection_handler = None
        self.printer = None

    def start(self):
        """Start the server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True

        print(f"Server listening on {self.host}:{self.port}...")

        self.printer = ThreadPrinter(self.print_comand_input)
        self.printer.start()

        self.connection_handler = ConnectionsHandler(self.server_socket, self.printer.print)
        self.connection_handler.start()

        try:
            self.handle_input()
        except KeyboardInterrupt:
            print("shutdown")
            self.stop()
        finally:
            print("\nServer shut down\n")

    def stop(self):
        """Stop the server and clean up."""
        self.running = False
        if self.connection_handler:
            self.connection_handler.stop()
            self.connection_handler.join()
        if self.server_socket:
            self.server_socket.close()
        if self.printer:
            self.printer.stop()

    def print_commands(self):
        print()
        print("Commands:")
        print("---------------------")
        print("help")
        print("ls")
        print("end <connection id>")
        print("shutdown")
        print("---------------------")

    def handle_input(self):
        self.print_commands()
        while True:
            input_args = input("\nCommand: ").split(" ", 1)
            command = input_args[0]
            if command == "help":
                self.print_commands()
            elif command == "ls":
                self.print_connections()
            elif command == "end":
                if len(input_args) < 2:
                    print("end reqired id paramter!")
                else:
                    self.end_connection(input_args[1])
            elif command == "shutdown":
                self.stop()
            else:
                print(f"command \"{command}\" not found")

    def print_comand_input(self):
        if self.running:
            print("\nCommand: ", end="")

    def print_connections(self):
        print()
        print("Connections:")
        print("---------------------")
        if len(self.connection_handler.connections) > 0:
            for connection in self.connection_handler.connections:
                print(f"Connection: id:{connection.client_id} address: {connection.addr}")
        else:
            print("No active connection")
        print("---------------------")

    def end_connection(self, id):
        if id not in [str(c.client_id) for c in self.connection_handler.connections]:
            print(f"Connection with \"{id}\" id not found.\nUse ls command to check existing connections")
            return
        self.connection_handler.close_connection(int(id))
        print(f"Connection {id} closed")


if __name__ == "__main__":
    port, host = process_args("server")

    server = DiffieHellmanServer(host, port)
    server.start()
