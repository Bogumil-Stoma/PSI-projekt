import socket

PORT = 12345
HOST = '0.0.0.0'
MAX_BUF_SIZE = 160000

def main():
    print(f"Server listening on port {PORT}...")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, PORT))
        
        while True:
            data, address = s.recvfrom(MAX_BUF_SIZE)
            length = (data[0] << 8) | data[1]
            if length != len(data) - 2:
                print("Received datagram length mismatch")
            else:
                print(f"Received datagram of length {len(data)}")

            response = b"OK"
            s.sendto(response, address)

if __name__ == "__main__":
    main()
