#include <arpa/inet.h>
#include <err.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define SERVER_PORT 12345
#define BUFFER_SIZE 65535 // Maximum UDP buffer size
#define SERVER_RESPONSE_SIZE 128

#define bailout(s) { printf("Error: %s", s); err(1, s); exit(EXIT_FAILURE); }

int main() {
    int sock;
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len = sizeof(client_addr);
    unsigned char buffer[BUFFER_SIZE];

    // Create socket
    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock == -1) {
        bailout("socket");
    }

    // Bind socket to port
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(SERVER_PORT);
    if (bind(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) == -1) {
        close(sock);
        bailout("bind");
    }

    printf("Server is listening on port %d\n", ntohs(server_addr.sin_port));

    while (1) {

        // Receive datagram
        int recv_len = recvfrom(sock, buffer, BUFFER_SIZE, 0, (struct sockaddr *)&client_addr, &client_len);
        if (recv_len < 0) {
            perror("recvfrom");
            continue;
        }

        // Extract datagram size that is combination of first two bytes
        int declarated_size = (buffer[0] << 8) | buffer[1];

        // Verify datagram size
        if (declarated_size != recv_len) {
            printf("Mismatch in declarated size (%d) and actual size (%d)\n", declarated_size, recv_len);
            continue;
        }

        printf("Received datagram of size: %d\n", recv_len);

        // Send acknowledgment back to the client
        char response[SERVER_RESPONSE_SIZE];
        snprintf(response, sizeof(response), "Received %d bytes", recv_len);
        if (sendto(sock, response, strlen(response), 0, (struct sockaddr *)&client_addr, client_len) == -1) {
            perror("sendto");
        }
    }

    close(sock);
    return 0;
}