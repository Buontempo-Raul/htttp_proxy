#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <netdb.h>
#include <http_parser.h>
#include <sys/socket.h>
#include <time.h>

#define BUFFER_SIZE 8192
#define PROXY_PORT 8080
#define GUI_PORT 9090  // Port for GUI communication
#define INTERCEPT_PORT 9091  // Port for intercept toggle control
#define MAX_HISTORY 1000  // Maximum number of history entries

typedef struct {
    char method[8];
    char url[1024];
    char headers[BUFFER_SIZE];
    char body[BUFFER_SIZE];
    size_t body_length;
} http_request;

typedef struct {
    char method[8];
    char url[1024];
    char protocol[16];
    char host[256];
    time_t timestamp;
    char request_data[BUFFER_SIZE];
    char response_data[BUFFER_SIZE];
} history_entry;

http_request current_request;
history_entry history[MAX_HISTORY];
int history_count = 0;

int intercept_enabled = 1;
pthread_mutex_t intercept_lock;

// HTTP parser callback functions
int on_url(http_parser* parser, const char* at, size_t length) {
    strncat(current_request.url, at, length);
    return 0;
}

int on_header_field(http_parser* parser, const char* at, size_t length) {
    strncat(current_request.headers, at, length);
    return 0;
}

int on_header_value(http_parser* parser, const char* at, size_t length) {
    strncat(current_request.headers, ": ", sizeof(current_request.headers) - strlen(current_request.headers) - 1);
    strncat(current_request.headers, at, length);
    strncat(current_request.headers, "\r\n", sizeof(current_request.headers) - strlen(current_request.headers) - 1);
    return 0;
}

int on_body(http_parser* parser, const char* at, size_t length) {
    strncat(current_request.body, at, length);
    current_request.body_length += length;
    return 0;
}

int on_message_complete(http_parser* parser) {
    return 0;
}

void parse_http_request(const char* request, size_t length) {
    http_parser parser;
    http_parser_init(&parser, HTTP_REQUEST);

    http_parser_settings settings;
    memset(&settings, 0, sizeof(settings));
    settings.on_url = on_url;
    settings.on_header_field = on_header_field;
    settings.on_header_value = on_header_value;
    settings.on_body = on_body;
    settings.on_message_complete = on_message_complete;

    memset(&current_request, 0, sizeof(current_request));
    http_parser_execute(&parser, &settings, request, length);
}

// Add an entry to the history
void add_to_history(const char* method, const char* url, const char* protocol, const char* host,
                    const char* request_data, const char* response_data) {
    pthread_mutex_lock(&intercept_lock);

    if (history_count < MAX_HISTORY) {
        history_entry* entry = &history[history_count++];
        strncpy(entry->method, method, sizeof(entry->method) - 1);
        strncpy(entry->url, url, sizeof(entry->url) - 1);
        strncpy(entry->protocol, protocol, sizeof(entry->protocol) - 1);
        strncpy(entry->host, host, sizeof(entry->host) - 1);
        entry->timestamp = time(NULL);
        strncpy(entry->request_data, request_data, sizeof(entry->request_data) - 1);
        strncpy(entry->response_data, response_data, sizeof(entry->response_data) - 1);
    }

    pthread_mutex_unlock(&intercept_lock);
}

// Send intercepted request or response to GUI and wait for decision
int communicate_with_gui(const char* message, const char* type) {
    int gui_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (gui_socket < 0) {
        perror("Failed to create socket");
        return 0;
    }

    struct sockaddr_in gui_addr;
    gui_addr.sin_family = AF_INET;
    gui_addr.sin_port = htons(GUI_PORT);
    inet_pton(AF_INET, "127.0.0.1", &gui_addr.sin_addr);

    if (connect(gui_socket, (struct sockaddr*)&gui_addr, sizeof(gui_addr)) < 0) {
        perror("Failed to connect to GUI");
        close(gui_socket);
        return 0;
    }

    // Send message type (REQUEST or RESPONSE) followed by actual message
    send(gui_socket, type, strlen(type), 0);
    send(gui_socket, "\n\n", 2, 0);  // Separator
    send(gui_socket, message, strlen(message), 0);

    char decision[BUFFER_SIZE];
    int n = recv(gui_socket, decision, sizeof(decision), 0);
    close(gui_socket);

    if (n > 0 && strncmp(decision, "FORWARD", 7) == 0) return 1;
    if (strcmp(type, "REQUEST") == 0) {
        printf("Request was dropped by the GUI\n");
    } else if (strcmp(type, "RESPONSE") == 0) {
        printf("Response was dropped by the GUI\n");
    }
    return 0;
}

void* handle_client(void* arg) {
    int client_socket = *(int*)arg;
    free(arg);

    char buffer[BUFFER_SIZE];
    int bytes_read = recv(client_socket, buffer, sizeof(buffer) - 1, 0);
    buffer[bytes_read] = '\0';

    parse_http_request(buffer, bytes_read);

    // Check intercept status
    pthread_mutex_lock(&intercept_lock);
    int intercept = intercept_enabled;
    pthread_mutex_unlock(&intercept_lock);

    char host[256];
    sscanf(current_request.headers, "Host: %s", host);

    char method[16] = "GET";  // Default method
    char protocol[16] = "HTTP";  // Default protocol

    // Parse method and URL
    sscanf(buffer, "%s %s %s", method, current_request.url, protocol);

    // If intercept is enabled, send request to GUI and check decision
    if (intercept && !communicate_with_gui(buffer, "REQUEST")) {
        close(client_socket);
        return NULL;  // Drop request if GUI decides so
    }

    // Forward the request to the destination server
    int server_socket;
    struct sockaddr_in server_addr;
    struct hostent* server = gethostbyname(host);
    if (!server) {
        perror("Host resolution failed");
        close(client_socket);
        return NULL;
    }

    server_socket = socket(AF_INET, SOCK_STREAM, 0);
    server_addr.sin_family = AF_INET;
    memcpy(&server_addr.sin_addr.s_addr, server->h_addr_list[0], server->h_length);
    server_addr.sin_port = htons(80);

    connect(server_socket, (struct sockaddr*)&server_addr, sizeof(server_addr));
    send(server_socket, buffer, bytes_read, 0);

    // Read the response from the server
    char response_buffer[BUFFER_SIZE];
    int response_size = 0;
    while ((response_size = recv(server_socket, response_buffer, sizeof(response_buffer), 0)) > 0) {
        response_buffer[response_size] = '\0';

        // Add to history
        add_to_history(method, current_request.url, protocol, host, buffer, response_buffer);

        // Intercept response if enabled
        if (intercept && !communicate_with_gui(response_buffer, "RESPONSE")) {
            break;
        }

        send(client_socket, response_buffer, response_size, 0);
    }

    close(server_socket);
    close(client_socket);
    return NULL;
}

void* intercept_control_listener(void* arg) {
    int intercept_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (intercept_socket < 0) {
        perror("Failed to create intercept control socket");
        return NULL;
    }

    struct sockaddr_in intercept_addr;
    intercept_addr.sin_family = AF_INET;
    intercept_addr.sin_addr.s_addr = INADDR_ANY;
    intercept_addr.sin_port = htons(INTERCEPT_PORT);

    if (bind(intercept_socket, (struct sockaddr*)&intercept_addr, sizeof(intercept_addr)) < 0) {
        perror("Failed to bind intercept control socket");
        close(intercept_socket);
        return NULL;
    }

    listen(intercept_socket, 1);
    printf("Intercept control listener running on port %d\n", INTERCEPT_PORT);

    while (1) {
        int control_socket = accept(intercept_socket, NULL, NULL);
        if (control_socket < 0) {
            perror("Failed to accept intercept control connection");
            continue;
        }

        char command[BUFFER_SIZE];
        int n = recv(control_socket, command, sizeof(command), 0);
        command[n] = '\0';

        if (strcmp(command, "INTERCEPT_ON") == 0) {
            pthread_mutex_lock(&intercept_lock);
            intercept_enabled = 1;
            pthread_mutex_unlock(&intercept_lock);
            printf("Intercept enabled by GUI\n");
        } else if (strcmp(command, "INTERCEPT_OFF") == 0) {
            pthread_mutex_lock(&intercept_lock);
            intercept_enabled = 0;
            pthread_mutex_unlock(&intercept_lock);
            printf("Intercept disabled by GUI\n");
        }

        close(control_socket);
    }

    close(intercept_socket);
    return NULL;
}

int create_server_socket(int port) {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in address = { .sin_family = AF_INET, .sin_addr.s_addr = INADDR_ANY, .sin_port = htons(port) };

    bind(server_fd, (struct sockaddr*)&address, sizeof(address));
    listen(server_fd, 10);
    return server_fd;
}

void accept_connections(int server_fd) {
    struct sockaddr_in client_addr;
    socklen_t client_addr_len = sizeof(client_addr);

    while (1) {
        int* client_socket = malloc(sizeof(int));
        *client_socket = accept(server_fd, (struct sockaddr*)&client_addr, &client_addr_len);
        pthread_t thread_id;
        pthread_create(&thread_id, NULL, handle_client, client_socket);
        pthread_detach(thread_id);
    }
}

int main() {
    pthread_mutex_init(&intercept_lock, NULL);

    int server_fd = create_server_socket(PROXY_PORT);
    printf("Proxy Server running on port %d\n", PROXY_PORT);

    pthread_t control_thread;
    pthread_create(&control_thread, NULL, intercept_control_listener, NULL);

    accept_connections(server_fd);

    close(server_fd);
    pthread_mutex_destroy(&intercept_lock);
    return 0;
}
