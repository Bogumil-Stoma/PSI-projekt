#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdbool.h>

#define DEFAULT_PORT 12345
#define DEFAULT_IP "127.0.0.1"
#define BUFFER_SIZE 102400 // 100 KB
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
    Node* head = NULL;
    Node* last = NULL;
    for (int i = 0; i < num_nodes; i++) {
        Node* current = (Node*)malloc(sizeof(Node));
        snprintf(current->text1, TEXT_SIZE, "Node %d Text1", i);
        snprintf(current->text2, TEXT_SIZE, "Node %d Text2 - but longer", i);

        if (last != NULL) {
            last->next = current;
        }
        last = current;
        if (head == NULL) {
            head = current;
        }
    }
    return head;
}

void add_string_to_stream(char *string, char *output_buffer, int *offset) {
    int string_size = strlen(string);
    uint32_t string_size_be = htonl(string_size);

    if (*offset + sizeof(string_size_be) + string_size > BUFFER_SIZE) {
        bailout("Buffer overflow in serialization");
    }

    // size of string
    memcpy(output_buffer + *offset, &string_size_be, sizeof(string_size_be));
    *offset += sizeof(string_size_be);

    // string
    memcpy(output_buffer + *offset, string, string_size);
    *offset += string_size;
}

void serialize_to_binary(Node *data_list, char *output_buffer, int *bytes_written) {
    int offset = 0;
    Node *current = data_list;
    while (current != NULL) {
        add_string_to_stream(current->text1, output_buffer, &offset);
        add_string_to_stream(current->text2, output_buffer, &offset);
        current = current->next;
    }
    *bytes_written = offset;
}


int main(int argc, char *argv[]) {

    int port = (argc >= 2) ? atoi(argv[1]) : DEFAULT_PORT;
    const char *ip = (argc == 3) ? argv[2] : DEFAULT_IP;

    int sockfd;
    if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        bailout("Socket creation failed");
    }

    int buff_size = BUFFER_SIZE;
    if (setsockopt(sockfd, SOL_SOCKET, SO_SNDBUF, &buff_size, sizeof(buff_size)) < 0) {
        close(sockfd);
        bailout("Failed to set send buffer size");
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

    Node* list = create_list(1000);

    char binary_buffer[BUFFER_SIZE] = {0};
    int bytes_written = 0;

    serialize_to_binary(list, binary_buffer, &bytes_written);

    ssize_t sent_data = send(sockfd, binary_buffer, bytes_written, 0);
    printf("Binary data sent to server (%zd / %d bytes)\n", sent_data, bytes_written);

    Node* current = list;
    while (current != NULL) {
        Node* temp = current;
        current = current->next;
        free(temp);
    }

    close(sockfd);
    return 0;
}
