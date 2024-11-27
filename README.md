### HTTP Proxy Server 🚀

> Bine ați venit la **HTTP Proxy Server**! Acest proiect implementează un proxy HTTP care interceptează cererile și răspunsurile HTTP, permite editarea antetelor și a conținutului, aplică reguli de modificare și filtrează informațiile. De asemenea, include o interfață grafică în Python pentru gestionare ușoară.

---

### Table of Contents 📖
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [Connect to Browser](#connect-to-browser)
- [Graphical Interface](#graphical-interface)

---

## Features 🌐

- **Interceptare Cereri**: Interceptează cererile HTTP de la clienți.
- **Editare Antete**: Permite modificarea antetelor HTTP.
- **Modificare Conținut**: Reguli personalizate pentru modificarea răspunsurilor HTTP.
- **Filtrare Conținut**: Filtrare bazată pe reguli definite.
- **Modificare Link-uri**: Schimbă link-urile din răspunsuri pentru redirecționare.
- **Interfață Grafică**: Permite gestionarea ușoară a cererilor și răspunsurilor.

---

## Technologies Used 👨‍💻

- **C**: Limbaj principal pentru implementarea proxy-ului.
- **Python (Tkinter)**: Folosit pentru interfața grafică.
- **Socket Programming**: Gestionează comunicațiile între client și server.
- **Linux**: Sistem de operare utilizat pentru rularea proxy-ului.

---

## Setup and Installation 💻

1. Clonați repository-ul:
    ```bash
    git clone https://github.com/username/http_proxy.git
    ```
2. Navigați în directorul proiectului:
    ```bash
    cd http_proxy
    ```
3. Instalați biblioteca http_parser:
   - Pentru majoritatea distribuțiilor Linux (Ubuntu/Debian), utilizați comanda:
   ```bash
   sudo apt-get install libhttp-parser-dev
   ```
   - Pentru alte distribuții sau dacă http_parser nu este inclus în managerul de pachete, instalați-l din surse:
   ```bash
   git clone https://github.com/nodejs/http-parser.git
   cd http-parser
   make
   sudo make install
   ```
4. Compilați codul proxy-ului:
    ```bash
    gcc -o http_proxy http_proxy.c -lhttp_parser -lpthread
    ```

5. Instalați dependențele pentru interfața grafică:
    ```bash
    pip install tkinter
    ```

---

## Usage 🧰

1. Rulați serverul proxy HTTP:
    ```bash
    ./http_proxy
    ```

2. Porniți interfața grafică:
    ```bash
    python3 gui.py
    ```

---

## Connect to Browser 🌐

1. Configurați manual setările proxy din browser:
    - **Adresă**: `localhost`
    - **Port**: `8080`

2. Dacă browser-ul nu permite setarea manuală a proxy-ului, puteți testa proxy-ul folosind comanda `curl`:
    ```bash
    curl -x localhost:8080 http://example.com
    ```

---

## Graphical Interface 🖥️

Interfața grafică este implementată în **Python** folosind biblioteca **Tkinter**. Aceasta permite:
- Vizualizarea antetelor și a corpului cererilor/răspunsurilor HTTP.
- Modificarea și interceptarea traficului.
- Gestionarea istorică a cererilor/răspunsurilor.
- Decizii rapide de tip *Forward* sau *Drop* pentru cereri și răspunsuri.
Pentru a folosi interfața, asigurați-vă că serverul proxy rulează înainte de a lansa GUI-ul.

### Funcționalități Interfață:
- **Tab Cereri**: Vizualizați și modificați antetele și conținutul cererilor HTTP.
- **Tab Răspunsuri**: Vizualizați și modificați antetele și conținutul răspunsurilor HTTP.
- **Tab Istoric**: Consultați istoricul cererilor/răspunsurilor procesate.
- **Control Interceptare**: Activați sau dezactivați interceptarea traficului în timp real.
