#include <arpa/inet.h>
#include <err.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define DEFAULT_PORT 12345
#define BUFFER_SIZE 65535
#define SERVER_RESPONSE_SIZE 128

void bailout(const char *msg)
{
    perror(msg);
    exit(EXIT_FAILURE);
}

int setup_socket(int port)
{
    int sock;
    struct sockaddr_in server_addr;

    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock == -1)
        bailout("socket");

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(port);

    if (bind(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) == -1)
    {
        close(sock);
        bailout("bind");
    }

    printf("Server is listening on port %d\n", port);
    return sock;
}

void handle_client(int sock)
{
    struct sockaddr_in client_addr;
    socklen_t client_len = sizeof(client_addr);
    unsigned char buffer[BUFFER_SIZE];

    int recv_len = recvfrom(sock, buffer, BUFFER_SIZE, 0, (struct sockaddr *)&client_addr, &client_len);
    if (recv_len < 0)
    {
        perror("recvfrom");
        return;
    }

    int declarated_size = (buffer[0] << 8) | buffer[1];

    if (declarated_size != recv_len)
    {
        printf("Mismatch in declared size (%d) and actual size (%d)\n", declarated_size, recv_len);
        return;
    }

    printf("Received datagram of size: %d\n", recv_len);

    char response[SERVER_RESPONSE_SIZE];
    snprintf(response, sizeof(response), "Received %d bytes", recv_len);
    if (sendto(sock, response, strlen(response), 0, (struct sockaddr *)&client_addr, client_len) == -1)
    {
        perror("sendto");
    }
}

int parse_args(int argc, char *argv[])
{
    if (argc > 2)
    {
        fprintf(stderr, "Too many arguments provided. Usage: %s [PORT]\n", argv[0]);
        exit(EXIT_FAILURE);
    }
    return argc == 2 ? atoi(argv[1]) : DEFAULT_PORT;
}

int main(int argc, char *argv[])
{
    int port = parse_args(argc, argv);
    int sock = setup_socket(port);

    while (1)
    {
        handle_client(sock);
    }

    close(sock);
    return 0;
}
