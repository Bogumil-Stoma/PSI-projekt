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

typedef struct Node {
    char text1[50];
    char text2[50];
    struct Node* next;
} Node;

void bailout(const char *msg) {
    perror(msg);
    exit(EXIT_FAILURE);
}

Node* create_list() {
    Node* head = (Node*)malloc(sizeof(Node));
    strcpy(head->text1, "FirstNodeText1");
    strcpy(head->text2, "FirstNodeText2");

    Node* second = (Node*)malloc(sizeof(Node));
    strcpy(second->text1, "SecondNodeText1");
    strcpy(second->text2, "SecondNodeText2");
    head->next = second;

    Node* third = (Node*)malloc(sizeof(Node));
    strcpy(third->text1, "ThirdNodeText1");
    strcpy(third->text2, "ThirdNodeText2");
    second->next = third;
    third->next = NULL;

    return head;
}

void send_list(int sockfd, Node* head) {
    Node* current = head;
    while (current != NULL) {
        char buffer[BUFFER_SIZE];
        int text1_len = strlen(current->text1);
        int text2_len = strlen(current->text2);

        send(sockfd, &text1_len, sizeof(int), 0);
        send(sockfd, current->text1, text1_len, 0);

        send(sockfd, &text2_len, sizeof(int), 0);
        send(sockfd, current->text2, text2_len, 0);

        current = current->next;
    }

    int end_marker = 0;
    send(sockfd, &end_marker, sizeof(int), 0);
}


int main(int argc, char *argv[]) {
    int port = (argc >= 2) ? atoi(argv[1]) : DEFAULT_PORT;
    const char *ip = (argc == 3) ? argv[2] : DEFAULT_IP;

    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock == -1) {
        bailout("socket creation failed");
    }

    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr);

    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);
    if (inet_pton(AF_INET, ip, &server_addr.sin_addr) <= 0) {
        close(sock);
        bailout("Invalid server IP address");
    }

    if (connect(sockfd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        close(sockfd);
        bailout("Connection failed");
    }

    printf("Connected on %s\n", ip);

    Node* list = create_list();
    send_list(sockfd, list);

    printf("Data sent to server successfully.\n");

    close(sock);
    return 0;
}