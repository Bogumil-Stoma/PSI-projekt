#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdbool.h>

#define HEADER_SIZE 2
#define SERVER_RESPONSE_SIZE 128
#define BYTES_ITERATION_SIZE 1000
#define ITERATIONS 100
#define DEFAULT_PORT 12345
#define DEFAULT_IP "127.0.0.1"
#define MESSAGE "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

void bailout(const char *msg) {
    perror(msg);
    exit(EXIT_FAILURE);
}

void prepare_datagram(unsigned char *buffer, int size) {
    buffer[0] = (size >> 8) & 0xFF;
    buffer[1] = size & 0xFF;
    int i;
    for (i = HEADER_SIZE; i < size; i++) {
        buffer[i] = MESSAGE[(i - HEADER_SIZE) % strlen(MESSAGE)];
    }
}

bool send_and_receive(int sock, struct sockaddr_in *server_addr, int size) {
    unsigned char *buffer = (unsigned char *)malloc(size);
    if (!buffer) {
        bailout("malloc failed");
        return false;
    }

    prepare_datagram(buffer, size);

    if (sendto(sock, buffer, size, 0, (struct sockaddr *)server_addr, sizeof(*server_addr)) == -1) {
        free(buffer);
        printf("sendto failed");
        return false;
    }

    char response[SERVER_RESPONSE_SIZE];
    int recv_len = recvfrom(sock, response, sizeof(response), 0, NULL, NULL);
    if (recv_len == -1) {
        free(buffer);
        bailout("recvfrom failed");
        return false;
    }

    printf("Sent datagram of size: %d, received response: %.*s\n", size, recv_len, response);
    free(buffer);
    return true;
}

int main(int argc, char *argv[]) {
    int port = (argc >= 2) ? atoi(argv[1]) : DEFAULT_PORT;
    const char *ip = (argc == 3) ? argv[2] : DEFAULT_IP;

    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock == -1) {
        bailout("socket creation failed");
    }

    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);
    if (inet_pton(AF_INET, ip, &server_addr.sin_addr) <= 0) {
        close(sock);
        bailout("Invalid server IP address");
    }

    printf("Client started, sending datagrams to %s:%d\n", ip, port);
    int datagram_size, i, j;
    for (i = 1; i < ITERATIONS; i++) {
        datagram_size = i * BYTES_ITERATION_SIZE;
        if (!send_and_receive(sock, &server_addr, datagram_size)){
            printf("idk some fail");
            break;
        }
    }
    int start = datagram_size - BYTES_ITERATION_SIZE;
    printf("Initial datagram size: %d\n", datagram_size);
    for (j = 1; j < BYTES_ITERATION_SIZE; j++) {
        datagram_size = start + j;
        if (!send_and_receive(sock, &server_addr, datagram_size)){
            break;
	    exit(EXIT_FAILURE);
        }
    }

    close(sock);
    return 0;
}
