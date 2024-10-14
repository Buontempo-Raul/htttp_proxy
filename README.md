# HTTP Proxy Server 🚀

> Bine ați venit la HTTP Proxy Server! Acest proiect implementează un proxy HTTP care interceptează cererile și răspunsurile HTTP, permite editarea antetelor și a conținutului, aplică reguli de modificare a conținutului și filtrează informațiile. 

### Table of Contents 📖
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Features 🌐

- **Interceptare Cereri**: Interceptează cererile HTTP de la clienți.
- **Editare Antete**: Permite modificarea antetelor HTTP.
- **Modificare Conținut**: Reguli pentru a modifica conținutul răspunsurilor.
- **Filtrare Conținut**: Filtrează răspunsurile în funcție de reguli definite.
- **Modificare Link-uri**: Schimbă link-urile din răspunsuri pentru a redirecționa utilizatorii.

## Technologies Used 👨‍💻

- **C**: Limbajul de programare utilizat pentru implementarea proxy-ului.
- **Socket Programming**: Folosit pentru gestionarea comunicațiilor între client și server.
- **Linux**: Sistem de operare pe care rulează proxy-ul.

## Setup and Installation 💻

1. Clonați repository-ul:
    ```bash
    git clone https://github.com/username/http_proxy.git
    ```
2. Navigați în directorul proiectului:
    ```bash
    cd http_proxy
    ```
3. Compilați proiectul: Proiectul conține trei componente: client, proxy și server. Fiecare trebuie să fie rulat pe terminale diferite. Utilizați comanda make pentru a compila toate componentele. În Makefile, veți găsi definițiile pentru fiecare componentă:
   ```bash
   all: client proxy server
   
   client: client.c
    gcc client.c -o client
   
   proxy: proxy.c   
    gcc proxy.c -o proxy
   
   server: server.c
    gcc server.c -o server
   ```
4. Compilați proiectul:
    ```bash
    make
    ```
## Usage 
> Rularea componentelor pe terminale separate:
- **Server:** Într-un prim terminal, rulați serverul:
   ```bash
  ./server
   ```
- **Proxy:** Într-un al doilea terminal, rulați proxy-ul HTTP:
  ```bash
  ./proxy
  ```
- **Client:** Într-un al treilea terminal, rulați clientul:
  ```bash
  ./client
  ```
