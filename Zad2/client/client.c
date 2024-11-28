#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdbool.h>

#define DEFAULT_PORT 12345
#define DEFAULT_IP "127.0.0.1"
#define BUFFER_SIZE 1024
#define TEXT_SIZE 50

typedef struct Node {
    char text1[TEXT_SIZE];
    char text2[TEXT_SIZE];
    struct Node* next;
} Node;

void bailout(const char *msg) {
    perror(msg);
    exit(EXIT_FAILURE);
}

Node* create_list(int num_nodes) {
    Node* head = (Node*)malloc(sizeof(Node));
    Node* current = head;

    for (int i = 0; i < num_nodes; i++) {

        snprintf(current->text1, TEXT_SIZE, "Node %d Text1", i);
        snprintf(current->text2, TEXT_SIZE, "Node %d Text2", i);

        if (i < num_nodes - 1) {
            current->next = (Node*)malloc(sizeof(Node));
            current = current->next;
        } else {
            current->next = NULL;
        }
    }
    return head;
}


void send_list(int sockfd, Node* head) {
    Node* current = head;
    while (current != NULL) {
        char buffer[BUFFER_SIZE];
        int text1_len = strlen(current->text1);
        uint32_t text1_len_be = htonl(text1_len);
        int text2_len = strlen(current->text2);
        uint32_t text2_len_be = htonl(text2_len);

        send(sockfd, &text1_len_be, sizeof(int), 0);
        send(sockfd, current->text1, text1_len, 0);

        send(sockfd, &text2_len_be, sizeof(int), 0);
        send(sockfd, current->text2, text2_len, 0);

        current = current->next;
    }

    int end_marker = 0;
    send(sockfd, &end_marker, sizeof(int), 0);
}


int main(int argc, char *argv[]) {

    int port = (argc >= 2) ? atoi(argv[1]) : DEFAULT_PORT;
    const char *ip = (argc == 3) ? argv[2] : DEFAULT_IP;

    int sockfd;
    if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        bailout("Socket creation failed");
    }

    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);
    if (inet_pton(AF_INET, ip, &server_addr.sin_addr) <= 0) {
        close(sockfd);
        bailout("Invalid server IP address");
    }

    if (connect(sockfd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        close(sockfd);
        bailout("Connection failed");
    }

    printf("Connected on %s\n", ip);

    Node* list = create_list(3);
    send_list(sockfd, list);

    printf("Data sent to server successfully.\n");

    Node* current = list;
    while (current != NULL) {
        Node* temp = current;
        current = current->next;
        free(temp);
    }

    close(sockfd);
    return 0;
}
