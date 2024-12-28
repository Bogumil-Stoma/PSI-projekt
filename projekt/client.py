import socket
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

        server_hello = receive_data(self.client_socket, 15)  # 11 + 16 + 8 + 8
        _, server_public_key = struct.unpack("!11sI", server_hello)

        print(f"Received ServerHello with B={server_public_key}")

        shared_key = calculate_shared_key(server_public_key, private_key, self.p)
        symmetric_key = derive_symmetric_key(shared_key)

        print(f"Shared key K computed: {shared_key}, Symmetric key derived.")
        return symmetric_key

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(10)
            print(f"Connecting to server at {self.host}:{self.port}...")
            self.client_socket.connect((self.host, self.port))
            print("Connected")
            self.symmetric_key = self.perform_key_exchange(self.private_key, self.public_key)
            self.connected = True
        except Exception as e:
            print(f"Connection error: {e}")

    def dissconnect(self):
        self.client_socket.close()
        self.connected = False
        print("disconnected")

    def send_message(self, message):
        try:
            print("Connected to the server.")

            print(f"Sending: {message}")

            send_string(self.client_socket, message)
            #response = read_string(self.client_socket)
            #print(f"Received: {response}")

        except ConnectionError:
            print("Lost connection to the server.")
            self.connected = False
        except Exception as e:
            print(f"Error: {e}")
            self.connected = False

    def print_commands(self):
        print()
        print("Commands:")
        print("---------------------")
        print("connect")
        print("send <message content>")
        print("end")
        print("---------------------")

    def start(self):
        self.private_key = generate_private_key()
        self.public_key = calculate_public_key(self.g, self.private_key, self.p)

        self.connected = False
        self.print_commands()
        while True:
            input_args = input("\nCommand: ").split(" ", 1)
            command = input_args[0]
            if command == "connect":
                if (self.connected):
                    print("Already connected!")
                else:
                    self.connect()
            elif command == "send":
                if (not self.connected):
                    print("Serwer not connected! use connect command")
                elif len(input_args) < 2:
                    print("send reqired message as paramter!")
                else:
                    self.send_message(input_args[1])
            elif command == "end":
                if (not self.connected):
                    print("Serwer not connected!  use connect command")
                else:
                    self.dissconnect()
            else:
                print(f"command \"{command}\" not found")


if __name__ == "__main__":
    port, host = process_args("client")
    client = DiffieHellmanClient(host, port, 5, 23)
    client.start()