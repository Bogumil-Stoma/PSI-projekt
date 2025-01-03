from typing import Callable, Self
import socket
import threading
import struct
import utils
import sys
import os
import time

class Connection(threading.Thread):
    def __init__(self, client_id, client_socket: socket.socket, addr,
                 remove_callback: Callable[[Self], None],
                 printer: utils.ThreadPrinter, verbose):
        super().__init__()
        self.client_id = client_id
        self.client_socket = client_socket
        self.addr = addr
        self.remove_callback = remove_callback
        self.printer = printer
        self.p = None
        self.g = None
        self.stop_event = threading.Event()
        self.verbose = verbose

    def print(self, *args):
        self.printer.print(f"Client {self.client_id}: ", end="")
        self.printer.print(*args)

    def print_if_verbose(self, *args):
        if self.verbose:
            self.print(*args)

    def execute_if_verbose(self, func, *args):
        if self.verbose:
            func(*args)

    def run(self):
        """Handle the client logic."""
        try:
            self.symmetric_key = self.perform_key_exchange()
            self.handle_client_message()
        except Exception as e:
            self.print(f"Caught error with client {self.client_id}: {e}")

    def stop(self, if_remove_from_connections=True):
        """Close the connection and clean up."""
        self.client_socket.close()
        self.print(f"Connection with {self.addr} closed.")
        if if_remove_from_connections:
            self.remove_callback(self)
        self.stop_event.set()

    def perform_key_exchange(self):
        self.print("Waiting for ClientHello")
        client_hello = utils.receive_data(self.client_socket, 23)
        client_hello_msg, client_public_key, self.p, self.g = struct.unpack("!11sIII", client_hello)

        self.print_if_verbose(f"[V] Received ClientHello with msg={client_hello_msg.decode()}")
        self.print_if_verbose(f"[V] Received ClientHello with A={client_public_key} "
                              f"p={self.p} g={self.g}")

        server_private_key = utils.generate_private_key()
        server_public_key = utils.calculate_public_key(self.g, server_private_key, self.p)

        self.print_if_verbose(f"[V] Sending ServerHello with B={server_public_key}")
        hello_message = struct.pack("!11sI", b"ServerHello", server_public_key)
        self.client_socket.sendall(hello_message)

        shared_key = utils.calculate_shared_secret(client_public_key, server_private_key, self.p)
        symmetric_key = utils.derive_symmetric_key(shared_key)

        self.print_if_verbose(f"[V] Shared key K computed: {shared_key}.")
        self.print_if_verbose(f"[V] Symmetric key derived: {symmetric_key.hex()}.")

        return symmetric_key

    def handle_client_message(self):
        self.print("Connection was established - waiting for messages from the client.")
        while not self.stop_event.is_set():
            message_size_data = utils.receive_data(self.client_socket, 4)
            message_size = struct.unpack("!I", message_size_data)[0]
            iv = utils.receive_data(self.client_socket, utils.AES_BLOCK_SIZE) # 16B
            ciphertext = utils.receive_data(self.client_socket, message_size)
            mac = utils.receive_data(self.client_socket, 32) # 32B

            calculated_mac = utils.calculate_hmac(ciphertext, self.symmetric_key)
            if mac != calculated_mac:
                self.print("Authentication failed")
                self.print("MAC received: ", mac, "\nMAC calculated: ", calculated_mac)

                self.send_message(utils.ServerMessages.FAIL)
                self.stop()

                return

            decrypted_message = utils.aes_cbc_decrypt(iv, ciphertext, self.symmetric_key)

            self.print(f"Received text: {decrypted_message}")
            self.print_if_verbose(f"[V] Received message size: {message_size}")
            self.print_if_verbose(f"[V] Received IV: {iv.hex()}")
            self.print_if_verbose(f"[V] Received ciphertext: {ciphertext.hex()}")
            self.print_if_verbose(f"[V] Received MAC: {mac.hex()}")

            if decrypted_message == utils.ServerMessages.END_SESSION:
                self.stop()
                return

            self.send_message(utils.ServerMessages.OK)

    def send_message(self, message):
        try:
            self.print(f"Sending: {message}")

            iv = os.urandom(utils.AES_BLOCK_SIZE) # random 16B

            ciphertext = utils.aes_cbc_encrypt(iv, message, self.symmetric_key)
            message_size = struct.pack("!I", len(ciphertext))

            mac = utils.calculate_hmac(ciphertext, self.symmetric_key) # 32B
            final_message = message_size + iv + ciphertext + mac

            self.print_if_verbose(f"[V] Sent text (length: {len(message)}): {message.value}")
            self.print_if_verbose(f"[V] Sent ciphertext (length: {len(ciphertext)}): "
                                  f"{ciphertext.hex()}")
            self.print_if_verbose(f"[V] Sent IV: {iv.hex()}")
            self.print_if_verbose(f"[V] Sent MAC: {mac.hex()}")

            self.client_socket.sendall(final_message)
        except ConnectionError:
            self.print("Lost connection to the client.")
            self.stop()
        except Exception as e:
            self.print(f"Caught Error while sending the message to client: {e}")
            self.stop()
            raise e

class ConnectionsHandler(threading.Thread):
    def __init__(self, server_socket: socket.socket, printer: utils.ThreadPrinter,
                 verbose, timeout=1.0):
        super().__init__()
        self.server_socket = server_socket
        self.printer = printer
        self.timeout = timeout
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.next_client_id = 0
        self.verbose = verbose
        self.connections: list[Connection] = []

    def print(self, *args):
        self.printer.print("ConnectionsHandler: ", end="")
        self.printer.print(*args)

    def run(self):
        """Accept connections in a loop until stopped."""
        self.server_socket.settimeout(self.timeout)
        try:
            while not self.stop_event.is_set():
                try:
                    client_socket, addr = self.server_socket.accept()
                    self.print(f"Connection {self.next_client_id} will be established with {addr}")
                    connection = Connection(self.next_client_id,
                                            client_socket,
                                            addr,
                                            self.remove_connection,
                                            self.printer,
                                            self.verbose)
                    self.connections.append(connection)
                    self.next_client_id += 1
                    connection.start()
                except socket.timeout:
                    continue
        except Exception as e:
            self.print(f"Caught Error: {e}")
        finally:
            self.print("Stopped")

    def stop(self):
        """Stop accepting connections."""
        self.stop_event.set()
        self.join()
        self.close_all_connections() # thread is stopped, this is executed from main thread

    def remove_connection(self, connection):
        """Remove a connection from the active list."""
        if self.stop_event.is_set():
            return
        with self.lock:
            if connection in self.connections:
                self.connections.remove(connection)

    def close_all_connections(self):
        self.print("Closing all connections")
        with self.lock:
            for connection in self.connections:
                connection.send_message(utils.ServerMessages.END_SESSION)
                time.sleep(0.1) # give client time to read the message
                connection.stop(False)
                connection.join()
            self.connections = []

    def close_connection(self, id):
        """Close a specific connection by id."""
        with self.lock:
            for connection in self.connections:
                if connection.client_id == id:
                    connection.send_message(utils.ServerMessages.END_SESSION)
                    time.sleep(0.1) # give client time to read the message
                    connection.stop(False)
                    connection.join()
                    self.connections.remove(connection)
                    break


class DiffieHellmanServer:
    def __init__(self, host, port, verbose):
        self.host = host
        self.port = port
        self.server_socket = None
        self.connection_handler = None
        self.verbose = verbose
        self.printer = utils.ThreadPrinter()
        self.printer.start()

    def print(self, *args, **kwargs):
        self.printer.print(*args, **kwargs)

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        self.print(f"Server listening on {self.host}:{self.port}...")
        self.connection_handler = ConnectionsHandler(self.server_socket, self.printer,
                                                     self.verbose, timeout=10.0)
        self.connection_handler.start()

        try:
            self.handle_input()
        except KeyboardInterrupt:
            self.connection_handler.close_all_connections()
            self.stop()
            self.print("Shutting down server...")
            sys.exit(0)
        finally:
            self.print("Server shut down\n")

    def stop(self):
        """Stop the server and clean up."""
        if self.connection_handler:
            self.connection_handler.stop()
            self.connection_handler.join()
        if self.printer:
            self.printer.stop()
            self.printer.join()
        if self.server_socket:
            self.server_socket.close()

    def print_commands(self):
        self.print("Commands:")
        self.print("---------------------")
        self.print("help")
        self.print("ls")
        self.print("end <connection id>")
        self.print("shutdown")
        self.print("---------------------")

    def handle_input(self):
        self.print_commands()
        while True:
            input_args = input().split(" ", 1)
            command = input_args[0]
            if command == "help":
                self.print_commands()
            elif command == "ls":
                self.print_connections()
            elif command == "end":
                if len(input_args) < 2:
                    self.print("end reqired id paramter!")
                else:
                    self.end_connection(input_args[1])
            elif command == "shutdown":
                self.print("Shutting down server. It will take a moment...")
                self.connection_handler.close_all_connections()

                self.stop()
                sys.exit(0)
            else:
                self.print(f"Command '{command}' not found")

    def print_connections(self):
        self.print()
        self.print("Connections:")
        self.print("---------------------")
        if len(self.connection_handler.connections) > 0:
            for connection in self.connection_handler.connections:
                self.print(f"Connection: id:{connection.client_id}, address: {connection.addr}")
        else:
            self.print("No active connection")
        self.print("---------------------")

    def end_connection(self, id):
        if id not in [str(c.client_id) for c in self.connection_handler.connections]:
            self.print(f"Connection with \"{id}\" id not found.\n"
                       "Use 'ls' command to check existing connections")
            return

        self.connection_handler.close_connection(int(id))
        self.print(f"Connection {id} closed")


if __name__ == "__main__":
    port, host, verbose = utils.process_args("server")
    server = DiffieHellmanServer(host, port, verbose)
    server.start()
