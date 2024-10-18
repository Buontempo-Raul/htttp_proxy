#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <netdb.h>


#define PORT 8080
#define BUF_SIZE 8192

// Functii pentru optiuni de meniu
void intercept_traffic();
void edit_headers();
void modify_content_rules();
void filter_content();
void modify_links();

// Functie pentru a trimite cererea catre server si primire raspuns
void forward_to_server(int client_socket, char *request) {
    int server_socket;
    struct sockaddr_in server_addr;
    struct hostent *server;
    char buffer[BUF_SIZE];

    // Extragem domeniul din cererea HTTP (presupunand ca cererea e HTTP GET)
    char host[256];
    sscanf(request, "GET http://%255[^/] ", host); // Extragem domeniul web

    // Rezolvam adresa IP a serverului pe baza domeniului
    server = gethostbyname(host);
    if (server == NULL) {
        perror("Eroare la rezolvarea domeniului");
        return;
    }

    // Configuram socketul pentru a se conecta la server
    server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket < 0) {
        perror("Eroare la crearea socket-ului pentru server");
        return;
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(80); // HTTP foloseste portul 80
    memcpy(&server_addr.sin_addr.s_addr, server->h_addr_list[0], server->h_length);


    // Ne conectam la server
    if (connect(server_socket, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Eroare la conectarea la serverul web");
        close(server_socket);
        return;
    }

    // Trimitem cererea HTTP catre server
    send(server_socket, request, strlen(request), 0);

    // Primesc raspunsul de la server si il trimitem inapoi clientului
    int bytes_received;
    while ((bytes_received = recv(server_socket, buffer, BUF_SIZE, 0)) > 0) {
        send(client_socket, buffer, bytes_received, 0);
    }

    close(server_socket);
}

void *handle_client(void *arg) {
    int client_socket = *((int *)arg);
    free(arg);
    char buffer[BUF_SIZE];
    int bytes_received;

    // Primirea cererii de la client
    bytes_received = recv(client_socket, buffer, BUF_SIZE - 1, 0);
    if (bytes_received < 0) {
        perror("Eroare la primirea cererii de la client");
        close(client_socket);
        return NULL;
    }

    buffer[bytes_received] = '\0'; // Asiguram terminarea stringului

    printf("Cerere interceptata:\n%s\n", buffer);

    forward_to_server(client_socket, buffer);

    // Logica pentru a modifica cererile HTTP, anteturile si continutul

    close(client_socket);
    return NULL;
}

void start_proxy() {
    int server_socket, *client_socket;
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_addr_size = sizeof(client_addr);

    // Creare socket
    server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket < 0) {
        perror("Eroare la crearea socket-ului");
        exit(EXIT_FAILURE);
    }

    // Configurarea serverului
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    server_addr.sin_addr.s_addr = INADDR_ANY;

    // Binding
    if (bind(server_socket, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Eroare la bind");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    // Ascultam pentru conexiuni
    if (listen(server_socket, 10) < 0) {
        perror("Eroare la listen");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    printf("Proxy-ul HTTP ruleaza pe portul %d...\n", PORT);

    // Loop pentru acceptarea conexiunilor
    while (1) {
        client_socket = malloc(sizeof(int));
        *client_socket = accept(server_socket, (struct sockaddr *)&client_addr, &client_addr_size);
        if (*client_socket < 0) {
            perror("Eroare la accept");
            free(client_socket);
            continue;
        }

        // Creare thread pentru a trata fiecare client
        pthread_t thread_id;
        if (pthread_create(&thread_id, NULL, handle_client, client_socket) != 0) {
            perror("Eroare la crearea thread-ului");
            free(client_socket);
            continue;
        }
        pthread_detach(thread_id); // Eliberam resursele thread-ului cand acesta se termina
    }

    close(server_socket);
}

void show_menu() {
    int option;
    while (1) {
        printf("\n=== Meniu HTTP Proxy ===\n");
        printf("1. Intercepteaza trafic HTTP\n");
        printf("2. Permite editare headere HTTP si continut\n");
        printf("3. Reguli de modificare de continut\n");
        printf("4. Filtre de continut\n");
        printf("5. Modificare link-uri\n");
        printf("6. Iesi\n");
        printf("Selecteaza o optiune: ");
        scanf("%d", &option);

        switch (option) {
            case 1:
                intercept_traffic();
                break;
            case 2:
                edit_headers();
                break;
            case 3:
                modify_content_rules();
                break;
            case 4:
                filter_content();
                break;
            case 5:
                modify_links();
                break;
            case 6:
                printf("Iesire din program.\n");
                exit(0);
            default:
                printf("Optiune invalida. Incearca din nou.\n");
        }
    }
}

void print_http_proxy_title() {
printf("//////////////////////////////////////////////////////////\n");
printf("// _   _ _____ _____ ____    ____                       //\n");
printf("//| | | |_   _|_   _|  _ \\  |  _ \\ _ __ _____  ___   _  //\n");
printf("//| |_| | | |   | | | |_) | | |_) | '__/ _ \\ \\/ / | | | //\n");
printf("//|  _  | | |   | | |  __/  |  __/| | | (_) >  <| |_| | //\n");
printf("//|_| |_| |_|   |_| |_|     |_|   |_|  \\___/_/\\_\\__,  / //\n");
printf("//                                               |___/  //\n");
printf("//////////////////////////////////////////////////////////\n");

}

// Functii pentru actiunile din meniu
void intercept_traffic() {
    printf("Interceptare trafic HTTP activata.\n");
    // Logica pentru a intercepta cererile si raspunsurile HTTP
}

void edit_headers() {
    printf("Editare headere HTTP activata.\n");
    //Logica pentru a permite editarea headerelor HTTP
}

void modify_content_rules() {
    printf("Aplicare reguli de modificare a continutului.\n");
    //Reguli de modificare pentru continut
}

void filter_content() {
    printf("Filtrare continut activata.\n");
    //Logica pentru filtrarea continutului
}

void modify_links() {
    printf("Modificare link-uri activata.\n");
    //Logica pentru modificarea link-urilor in continut
}

int main() {
    pthread_t proxy_thread;

   

    // Pornim proxy-ul intr-un thread separat
    if (pthread_create(&proxy_thread, NULL, (void *)start_proxy, NULL) != 0) {
        perror("Eroare la crearea thread-ului pentru proxy");
        exit(EXIT_FAILURE);
    }

    // Afisam meniul de interactiune
    print_http_proxy_title();
    show_menu();

    return 0;
}
