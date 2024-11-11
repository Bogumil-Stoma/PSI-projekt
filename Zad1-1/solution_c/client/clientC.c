#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define HEADER_SIZE 2
#define SERVER_PORT 12345
#define SERVER_IP "172.21.35.2"
#define MESSAGE "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
#define SERVER_RESPONSE_SIZE 128
#define BYTES_ITERATION_SIZE 1000
#define ITERATIONS 100

#define bailout(s) { printf("Fatal Error: %s", s); err(1, s); exit(EXIT_FAILURE); }

int main() {
    int sock;
    struct sockaddr_in server_addr;
    socklen_t addr_len = sizeof(server_addr);
    unsigned char *buffer;

    // Create socket
    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock == -1) {
        bailout("socket");
    }

    // Set up server address
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    if (inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr) <= 0) {
        close(sock);
        bailout("bind");
    }

    printf("Client started on port %d\n", ntohs(server_addr.sin_port));

    // Send datagrams of increasing size
    int interation;
    for (interation = 1; interation < ITERATIONS; interation++) {

        int datagram_size = interation * BYTES_ITERATION_SIZE;

        // Set buffer size
        buffer = (char *)malloc(datagram_size);
        if (!buffer) {
            perror("malloc");
            exit(EXIT_FAILURE);
        }

        // First 2 bytes for size
        buffer[0] = (datagram_size >> 8) & 0xFF;
        buffer[1] = datagram_size & 0xFF;

        // Fill rest of datagram with message
        int i;
        for (i = HEADER_SIZE; i < datagram_size; i++) {
            buffer[i] = MESSAGE[(i-HEADER_SIZE) % sizeof(MESSAGE)];
        }

        // Send datagram
        if (sendto(sock, buffer, datagram_size, 0, (struct sockaddr *)&server_addr, addr_len) == -1) {
            perror("sendto");
            free(buffer);
            break;
        }

        // Receive response from server
        char response[SERVER_RESPONSE_SIZE];
        int recv_len = recvfrom(sock, response, sizeof(response), 0, NULL, NULL);
        if (recv_len == -1) {
            perror("recvfrom");
            free(buffer);
            break;
        }

        printf("Sent datagram of size: %d, received response: %.*s\n", datagram_size, recv_len, response);

        free(buffer);

        // wait 500,000 microseconds = 0.5 seconds
        usleep(500000);
    }

    close(sock);
    return 0;
}
