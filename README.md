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
- [Possible Solutions](#possible-solutions)

---

## Features 🌐

- **Interceptare Cereri**: Interceptează cererile HTTP de la clienți.
- **Istoric Cereri**: Un istoric unde sunt afisate toate cererile ce au primit raspuns.
- **Coada de Cereri**: O coada unde sunt afisate cererile ce asteapta a fi procesate.
- **Oprire/Pornire Interceptare**: Un buton care permite oprirea/pornirea interceptarii.
- **Black list**: Lista in care pot fi introduse site-uri care sa nu poata fi accesate de utilizator.
- **Editare Antete**: Permite modificarea antetelor HTTP.
- **Filtrare Conținut**: Filtrare bazată pe reguli definite.
- **Modificare Link-uri**: Schimbă link-urile din răspunsuri pentru redirecționare.
- **Interfață Grafică**: Permite gestionarea ușoară a cererilor și răspunsurilor.

---

## Technologies Used 👨‍💻

- **C**: Limbaj principal pentru implementarea proxy-ului.
- **Python (Tkinter)**: Folosit pentru interfața grafică.
- **Socket Programming**: Gestionează comunicațiile între client și server.
- **Threading Programming**: Gestioneaza mai multi utilizatori contemporan.
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
4.Instalați biblioteca ssh:  
- Pentru majoritatea distribuțiilor Linux (Ubuntu/Debian), utilizați comanda:
  ```bash
   sudo apt-get install libssl-dev
   ```
5. Compilați codul proxy-ului:
    ```bash
    gcc -o http_proxy http_proxy.c -lhttp_parser -ljansson -lssl -lcrypto -lpthread
    ```

5. Instalați dependențele pentru interfața grafică:
    ```bash
    pip install tkinter
    ```
6. Modificati fisierul credentials adaugand username-ul si parola dorita:
    ```bash
    username:password
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
3. Folositi un web browser sau dintr-un terminal Linux:
   ```bash
   curl -U user:password -x localhost:port_number http://example.com
---

## Connect to Browser 🌐

1. Cautati setarile aferente server-ului proxy.
2. Configurați manual setările proxy din browser:
    - **Adresă**: `localhost`
    - **Port**: `8080`
3. Daca browser-ul web nu permite configurarea manuala folositi un terminal Linux.

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

---

## Possible Solutions 🔧

In caz ca nu functioneaza server-ul proxy incercati sa verificati urmatoarele aspecte:
1. Instalarea corecta a bibliotecilor necesare.
2. Fisierul **credentials.txt** contine username-ul si parola corecta.
3. Folositi comanda corecta in terminalul Linux.
4. Efectuati o cerere de tip http **NU** https.
