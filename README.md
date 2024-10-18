# HTTP Proxy Server 🚀

> Bine ați venit la HTTP Proxy Server! Acest proiect implementează un proxy HTTP care interceptează cererile și răspunsurile HTTP, permite editarea antetelor și a conținutului, aplică reguli de modificare a conținutului și filtrează informațiile. 

### Table of Contents 📖
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [Connect to Browser](#Browser-connect)
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
    cd htttp_proxy
    ```
3. Compilați proiectul:
    ```bash
    gcc http_proxy.c -o http_proxy
    ```
## Usage 🧰
> Rularea proxy-ului:
```bash
./http_proxy
```
## Browser Connect
**Intrati in setarile browser-ului si cautati setarea manuala a proxy-ului. Aici veti seta adresa la "localhost" si la portul 8080.**    
- **!!!Daca nu permite browser-ul aceasta optiune, puteti incerca prin a folosi din terminal comdanda**
```bash
curl -x localhost:8080 http://example.com
```

