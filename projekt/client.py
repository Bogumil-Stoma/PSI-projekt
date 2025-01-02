import socket
import struct
import os
import sys
import utils


# TODO:W oddzielnym wątku nasluchujemy na wiadmości od servera:
# - "OK" -> "Message authenticity verification failed."
# - "FAIL" -> "Message authenticity verified successfully."
# - "DISCONNECT" -> "Server disconnected. Closing connection."
# - w tym wątku wykorzystać instację ThreadPrinter do wypisywania komunikatów

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

        # TODO: trzeba odczytać od serwera ServerHello w oddzielnym wątku
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
            self.client_socket.settimeout(10)
            self.print(f"Connecting to server at {self.host}:{self.port}...")
            self.client_socket.connect((self.host, self.port))

            # TODO: już zestowione połączenie wykorzystać w oddzilym wątku do nasluchiwania na wiadmości od servera, podać isntację threadPrintera
            self.print("Connected")
            self.symmetric_key = self.perform_key_exchange(self.private_key, self.public_key)
            self.connected = True
        except Exception as e:
            self.print(f"Connection error: {e}")

    def close_connection(self):
        self.client_socket.close()
        self.connected = False

    def notify_and_dissconnect(self):
        # TODO: wysyłamy do serwera wiadomość "EndSession" żeby sobie zamknął gniazdo

        self.close_connection()
        self.print("Notififed server and disconnected")

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

            # TODO: czekamy na wiadomość od server OK / FAIL
            # najpierw czytamy 4B a potem resztę
            # OK -> "Message authenticity verification failed."
            # FAIL -> "Message authenticity verified successfully."
            # Zrobić to trzeba w oddzielnym wątku

        except ConnectionError:
            self.print("Lost connection to the server")
            self.connected = False
        except Exception as e:
            self.print(f"Error while sending the message to server: {e}")
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
                    # TODO: wyslić wiadmość do servera 'EndSession'
                    self.notify_and_dissconnect()
            elif command == "shutdown":
                if self.connected:
                    self.notify_and_dissconnect()
                self.print("Shutting down client...")
                sys.exit(0)

            else:
                self.print(f"Command \"{command}\" not found")

if __name__ == "__main__":
    port, host, verbose = utils.process_args("client")
    client = DiffieHellmanClient(host, port, verbose, 5, 23)
    client.start()
