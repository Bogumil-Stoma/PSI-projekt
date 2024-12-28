import random
from hashlib import sha256
import struct
import argparse

DEFAULT_PORT = 12345


def generate_private_key(bits=16):
    """Generate a private key."""
    return random.randint(2, 2**bits)


def calculate_public_key(g, private_key, p):
    """Calculate the public key A or B."""
    return pow(g, private_key, p)


def calculate_shared_key(public_key, private_key, p):
    """Calculate the shared secret key K."""
    return pow(public_key, private_key, p)


def derive_symmetric_key(shared_key):
    """Derive a symmetric key from the shared secret key using SHA-256."""
    return sha256(str(shared_key).encode()).digest()


def send_string(sock, text):
    """Send a string message to a socket."""
    encoded_text = text.encode()
    text_size = len(encoded_text)
    packed_size = struct.pack("!I", text_size)
    sock.sendall(packed_size + encoded_text)


def receive_data(sock, size):
    """Receive a fixed amount of data from a socket."""
    data = b""
    while len(data) < size:
        packet = sock.recv(size - len(data))
        if not packet:
            raise ConnectionError("Socket connection lost")
        data += packet
    return data


def send_hello_message(sock, message_type, public_key, p, g):
    """Send a formatted Hello message."""
    hello_message = struct.pack("!11s16s16s16s", message_type.encode(), str(public_key).encode(), str(p).encode(), str(g).encode())
    sock.sendall(hello_message)


def read_string(sock):
    size_data = sock.recv(4)
    if not size_data:
        return None
    text_size = struct.unpack("!I", size_data)[0]
    text_data = sock.recv(text_size)
    return text_data.decode()


def process_args(connection_type: str):
    if connection_type == "server":
        DEFAULT_HOST = "0.0.0.0"
        description = "Start server"
    elif connection_type == "client":
        DEFAULT_HOST = "127.0.0.1"
        description = "Start client"
    else:
        raise ValueError("Invalid connection type")
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--port", type=int, nargs="?",
                        help="Port to listen on (default: %(default)s)",
                        default=DEFAULT_PORT)
    parser.add_argument("--host", type=str,
                        help="Host to listen on (default: %(default)s)",
                        default=DEFAULT_HOST)
    args = parser.parse_args()

    return args.port, args.host