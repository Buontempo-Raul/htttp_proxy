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
#include <jansson.h>  // JSON parsing library
#include <openssl/bio.h>
#include <openssl/evp.h>

#define MAX_CREDENTIALS 100
#define MAX_USERNAME_LENGTH 50
#define MAX_PASSWORD_LENGTH 50
#define CREDENTIALS_FILE "credentials.txt"

#define BUFFER_SIZE 8192
#define PROXY_PORT 8080
#define GUI_PORT 9090  // Port for GUI communication
#define INTERCEPT_PORT 9091  // Port for intercept toggle control
#define BLOCKED_DOMAINS_PORT 9092  // Port for blocked domains update
#define MAX_HISTORY 1000
#define MAX_BLOCKED_DOMAINS 100

typedef struct {
    char username[MAX_USERNAME_LENGTH];
    char password[MAX_PASSWORD_LENGTH];
} Credential;

Credential valid_credentials[MAX_CREDENTIALS];
int credentials_count = 0;

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


char blocked_domains[MAX_BLOCKED_DOMAINS][256];
int blocked_domains_count = 0;
pthread_mutex_t blocked_domains_lock;

int is_domain_blocked(const char* host) {
    pthread_mutex_lock(&blocked_domains_lock);
    
    for (int i = 0; i < blocked_domains_count; i++) {
        if (strstr(host, blocked_domains[i]) != NULL) {
            pthread_mutex_unlock(&blocked_domains_lock);
            return 1;
        }
    }
    
    pthread_mutex_unlock(&blocked_domains_lock);
    return 0;
}

int load_credentials() {
    FILE* file = fopen(CREDENTIALS_FILE, "r");
    if (file == NULL) {
        perror("Failed to open credentials file");
        return 0;
    }

    credentials_count = 0;
    while (
        fscanf(file, "%49[^:]:%49s", 
            valid_credentials[credentials_count].username, 
            valid_credentials[credentials_count].password
        ) == 2 && 
        credentials_count < MAX_CREDENTIALS
    ) {
        credentials_count++;
    }

    fclose(file);
    printf("Loaded %d credentials\n", credentials_count);
    return credentials_count > 0;
}

int verify_authentication(const char* request) {
    
    const char* auth_line = strstr(request, "Proxy-Authorization: Basic ");
    if (auth_line == NULL) {
        return 0;  
    }

   
    const char* end_line = strchr(auth_line, '\r');
    if (end_line == NULL) end_line = strchr(auth_line, '\n');
    if (end_line == NULL) end_line = auth_line + strlen(auth_line);

    
    char auth_header[512];
    size_t line_length = end_line - auth_line;
    strncpy(auth_header, auth_line, line_length);
    auth_header[line_length] = '\0';

    
    const char* base64_token = auth_header + strlen("Proxy-Authorization: Basic ");

    
    BIO *bio, *b64;
    char* decoded_token = NULL;
    int decoded_length;

    
    b64 = BIO_new(BIO_f_base64());
    bio = BIO_new_mem_buf(base64_token, strlen(base64_token));
    bio = BIO_push(b64, bio);

    
    BIO_set_flags(bio, BIO_FLAGS_BASE64_NO_NL);

    
    decoded_token = malloc(strlen(base64_token));
    decoded_length = BIO_read(bio, decoded_token, strlen(base64_token));
    
    
    decoded_token[decoded_length] = '\0';

    
    BIO_free_all(bio);

    if (decoded_length <= 0) {
        free(decoded_token);
        return 0;
    }

    
    char* username = decoded_token;
    char* password = strchr(decoded_token, ':');
    
    if (password == NULL) {
        free(decoded_token);
        return 0;
    }
    
    *password = '\0';  
    password++;  

   
    for (int i = 0; i < credentials_count; i++) {
        if (strcmp(valid_credentials[i].username, username) == 0 && 
            strcmp(valid_credentials[i].password, password) == 0) {
            free(decoded_token);
            return 1;
        }
    }

    free(decoded_token);
    return 0;
}

void update_blocked_domains(const char* json_str) {
    pthread_mutex_lock(&blocked_domains_lock);
    
    
    blocked_domains_count = 0;
    
    
    json_error_t error;
    json_t* root = json_loads(json_str, 0, &error);
    
    if (root && json_is_array(root)) {
        size_t index;
        json_t* value;
        
        json_array_foreach(root, index, value) {
            if (json_is_string(value) && blocked_domains_count < MAX_BLOCKED_DOMAINS) {
                const char* domain = json_string_value(value);
                strncpy(blocked_domains[blocked_domains_count], domain, sizeof(blocked_domains[0]) - 1);
                blocked_domains_count++;
            }
        }
    }
    
    if (root) json_decref(root);
    
    pthread_mutex_unlock(&blocked_domains_lock);
    
    printf("Updated blocked domains. Total: %d\n", blocked_domains_count);
}

void* blocked_domains_listener(void* arg) {
    int blocked_domains_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (blocked_domains_socket < 0) {
        perror("Failed to create blocked domains socket");
        return NULL;
    }

    struct sockaddr_in blocked_domains_addr;
    blocked_domains_addr.sin_family = AF_INET;
    blocked_domains_addr.sin_addr.s_addr = INADDR_ANY;
    blocked_domains_addr.sin_port = htons(BLOCKED_DOMAINS_PORT);

    if (bind(blocked_domains_socket, (struct sockaddr*)&blocked_domains_addr, sizeof(blocked_domains_addr)) < 0) {
        perror("Failed to bind blocked domains socket");
        close(blocked_domains_socket);
        return NULL;
    }

    listen(blocked_domains_socket, 1);
    printf("Blocked domains listener running on port %d\n", BLOCKED_DOMAINS_PORT);

    while (1) {
        int control_socket = accept(blocked_domains_socket, NULL, NULL);
        if (control_socket < 0) {
            perror("Failed to accept blocked domains connection");
            continue;
        }

        char json_buffer[BUFFER_SIZE];
        int n = recv(control_socket, json_buffer, sizeof(json_buffer) - 1, 0);
        json_buffer[n] = '\0';

        update_blocked_domains(json_buffer);
        close(control_socket);
    }

    close(blocked_domains_socket);
    return NULL;
}

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

    
    send(gui_socket, type, strlen(type), 0);
    send(gui_socket, "\n\n", 2, 0);  
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

    char buffer_copy[BUFFER_SIZE];
    strncpy(buffer_copy, buffer, sizeof(buffer_copy) - 1);
    buffer_copy[sizeof(buffer_copy) - 1] = '\0';

    
    if (!verify_authentication(buffer_copy)) {
        const char* unauthorized_response = 
            "HTTP/1.1 401 Unauthorized\r\n"
            "WWW-Authenticate: Basic realm=\"Proxy\"\r\n"
            "Content-Type: text/plain\r\n\r\n"
            "Authentication required";
        send(client_socket, unauthorized_response, strlen(unauthorized_response), 0);
        close(client_socket);
        return NULL;
    }

    
    char host1[256];
    sscanf(current_request.headers, "Host: %s", host1);

    if (is_domain_blocked(host1)) {
        const char* blocked_response = "HTTP/1.1 403 Forbidden\r\nContent-Type: text/plain\r\n\r\nDomain is blocked by proxy";
        send(client_socket, blocked_response, strlen(blocked_response), 0);
        close(client_socket);
        return NULL;
    }

   
    pthread_mutex_lock(&intercept_lock);
    int intercept = intercept_enabled;
    pthread_mutex_unlock(&intercept_lock);

    char host[256];
    sscanf(current_request.headers, "Host: %s", host);

    char method[16] = "GET";  
    char protocol[16] = "HTTP"; 

   
    sscanf(buffer, "%s %s %s", method, current_request.url, protocol);

    
    if (intercept && !communicate_with_gui(buffer, "REQUEST")) {
        close(client_socket);
        return NULL; 
    }

    
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

    
    char response_buffer[BUFFER_SIZE];
    int response_size = 0;
    while ((response_size = recv(server_socket, response_buffer, sizeof(response_buffer), 0)) > 0) {
        response_buffer[response_size] = '\0';

       
        add_to_history(method, current_request.url, protocol, host, buffer, response_buffer);

     
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
    
    if (!load_credentials()) {
        fprintf(stderr, "Failed to load credentials. Exiting...\n");
        return 1;
    }

    pthread_mutex_init(&intercept_lock, NULL);
    pthread_mutex_init(&blocked_domains_lock, NULL);

    int server_fd = create_server_socket(PROXY_PORT);
    printf("Proxy Server running on port %d\n", PROXY_PORT);

    pthread_t control_thread, blocked_domains_thread;
    pthread_create(&control_thread, NULL, intercept_control_listener, NULL);
    pthread_create(&blocked_domains_thread, NULL, blocked_domains_listener, NULL);

    accept_connections(server_fd);

    close(server_fd);
    pthread_mutex_destroy(&intercept_lock);
    pthread_mutex_destroy(&blocked_domains_lock);
    return 0;
}
