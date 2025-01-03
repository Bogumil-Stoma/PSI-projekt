from typing import Optional, Callable
import socket
import struct
import os
import sys
import utils
import threading
import time


class ServerListener(threading.Thread):
    def __init__(self, client_socket: socket.socket, printer: utils.ThreadPrinter,
                 symmetric_key, close_connection_callback: Callable[[], None],
                 notify_and_disconnect_callback: Callable[[], None]):
        super().__init__()
        self.client_socket = client_socket
        self.printer = printer
        self.stop_event = threading.Event()
        self.symmetric_key = symmetric_key
        self.close_connection_callback = close_connection_callback
        self.notify_and_disconnect_callback = notify_and_disconnect_callback

    def print(self, *args, **kwargs):
        self.printer.print(*args, **kwargs)

    def stop(self):
        self.stop_event.set()

    def run(self):
        """Processes server messages. Activated after completing key exchange."""
        try:
            while not self.stop_event.is_set():
                message_size_data = utils.receive_data(self.client_socket, 4)
                message_size = struct.unpack("!I", message_size_data)[0]
                iv = utils.receive_data(self.client_socket, utils.AES_BLOCK_SIZE)  # 16B
                ciphertext = utils.receive_data(self.client_socket, message_size)
                mac = utils.receive_data(self.client_socket, 32)  # 32B

                calculated_mac = utils.calculate_hmac(ciphertext, self.symmetric_key)
                if mac != calculated_mac:
                    self.print("Authentication failed - something is wrong with the server")
                    self.print("MAC received: ", mac, "\nMAC calculated: ", calculated_mac)
                    self.notify_and_disconnect_callback()

                    return

                decrypted_message = utils.aes_cbc_decrypt(iv, ciphertext, self.symmetric_key)
                self.print(f"Received text: {decrypted_message}")

                if decrypted_message == utils.ServerMessages.OK:
                    self.print("[From Server] Message authenticity verified successfully.")
                elif decrypted_message == utils.ServerMessages.FAIL:
                    self.notify_and_disconnect_callback()
                    self.print("[From Server] Message authenticity verification failed.")
                    self.stop_event.set()
                elif decrypted_message == utils.ServerMessages.END_SESSION:
                    self.close_connection_callback()
                    self.print("[From Server] Session ended by server. Disconnecting...")
                    self.stop_event.set()
                else:
                    self.print(f"[From Server] Unknown message: {decrypted_message}")
        except Exception as e:
            self.print(f"Caught Error in ServerListener: {e}")
        finally:
            self.print("ServerListener stopped.")


class DiffieHellmanClient:
    def __init__(self, host, port, verbose, g, p):
        self.host = host
        self.port = port
        self.g = g
        self.p = p
        self.client_socket = None
        self.connected = False
        self.verbose = verbose
        self.printer = utils.ThreadPrinter()
        self.printer.start()
        self.server_listener: Optional[ServerListener] = None

    def stop(self):
        self.notify_and_dissconnect()
        if self.server_listener:
            self.server_listener.stop()
            self.server_listener.join()
        if self.printer:
            self.printer.stop()
            self.printer.join()

    def print(self, *args, **kwargs):
        self.printer.print(*args, **kwargs)

    def print_if_verbose(self, *args, **kwargs):
        if self.verbose:
            self.print(*args, **kwargs)

    def start(self):
        self.private_key = utils.generate_private_key()
        self.public_key = utils.calculate_public_key(self.g, self.private_key, self.p)

        try:
            self.handle_input()
        except KeyboardInterrupt:
            if self.connected:
                self.notify_and_dissconnect()
        finally:
            self.print("Client shut down\n")

    def perform_key_exchange(self, private_key, public_key):
        hello_message = struct.pack("!11sIII", b"ClientHello",
                                    public_key, self.p, self.g)
        self.client_socket.sendall(hello_message)
        self.print_if_verbose(f"[V] Sent ClientHello with A={public_key}, p={self.p}, g={self.g}")

        server_hello = utils.receive_data(self.client_socket, 15)  # 11 + 4
        server_hello_msg, server_public_key = struct.unpack("!11sI", server_hello)

        self.print_if_verbose(f"[V] Received ServerHello with msg={server_hello_msg.decode()}")
        self.print_if_verbose(f"[V] Received ServerHello with B={server_public_key}")

        shared_key = utils.calculate_shared_secret(server_public_key, private_key, self.p)
        symmetric_key = utils.derive_symmetric_key(shared_key)

        self.print_if_verbose(f"[V] Shared key K computed: {shared_key}")
        self.print_if_verbose(f"[V] Symmetric key derived: {symmetric_key.hex()}")

        return symmetric_key

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(None) # continuous listenening for messages
            self.print(f"Connecting to server at {self.host}:{self.port}...")
            self.client_socket.connect((self.host, self.port))

            self.symmetric_key = self.perform_key_exchange(self.private_key, self.public_key)
            self.print("Successfully connected to the server")
            self.connected = True

            self.server_listener = ServerListener(self.client_socket, self.printer,
                                                  self.symmetric_key, self.close_connection,
                                                  self.notify_and_dissconnect)
            self.server_listener.start()
        except Exception as e:
            self.print(f"Caught Connection Error: {e}")

    def close_connection(self):
        self.client_socket.close()
        self.connected = False

    def notify_and_dissconnect(self):
        if self.connected:
            self.send_message(utils.ServerMessages.END_SESSION) # notify server
            time.sleep(0.1) # give server time to read the message
            self.close_connection()
            self.print("Notififed server and disconnected")
        else:
            self.print("Client disconnected...")




    def send_message(self, message):
        try:
            self.print(f"Sending: {message}")

            iv = os.urandom(utils.AES_BLOCK_SIZE) # random 16B

            ciphertext = utils.aes_cbc_encrypt(iv, message, self.symmetric_key)
            message_size = struct.pack("!I", len(ciphertext))

            mac = utils.calculate_hmac(ciphertext, self.symmetric_key) # 32B
            final_message = message_size + iv + ciphertext + mac

            self.print_if_verbose(f"[V] Sent text (length: {len(ciphertext)}): {ciphertext.hex()}")
            self.print_if_verbose(f"[V] Sent IV: {iv.hex()}")
            self.print_if_verbose(f"[V] Sent MAC: {mac.hex()}")

            self.client_socket.sendall(final_message)

        except ConnectionError:
            self.print("Caught Error: lost connection to the server")
            self.connected = False
        except Exception as e:
            self.print(f"Caught Error while sending the message to server: {e}")
            self.connected = False
            raise e

    def print_commands(self):
        self.print("Commands:")
        self.print("---------------------")
        self.print("help")
        self.print("connect")
        self.print("send <message content>")
        self.print("end_connection")
        self.print("shutdown")
        self.print("---------------------")

    def handle_input(self):
        self.print_commands()
        while True:
            input_args = input().split(" ", 1)
            command = input_args[0]
            if command == "help":
                self.print_commands()
            elif command == "connect":
                if (self.connected):
                    self.print("Already connected!")
                else:
                    self.connect()
            elif command == "send":
                if (not self.connected):
                    self.print("Server not connected! Use 'connect' command")
                elif len(input_args) < 2:
                    self.print("Send required message paramter! (send <message content>)")
                else:
                    self.send_message(input_args[1].strip())
            elif command == "end_connection":
                if (not self.connected):
                    self.print("Server not connected!  Use 'connect' command")
                else:
                    self.notify_and_dissconnect()
            elif command == "shutdown":
                self.stop()
                self.print("Shutting down client...")
                sys.exit(0)

            else:
                self.print(f"Command \"{command}\" not found")

if __name__ == "__main__":
    port, host, verbose = utils.process_args("client")
    client = DiffieHellmanClient(host, port, verbose, 5, 23)
    client.start()
