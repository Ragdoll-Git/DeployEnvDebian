GUIA.md

Guía de Configuración: Entorno Docker para BrainBash
Esta guía detalla cómo levantar un entorno de desarrollo Debian + Python 3.11 + Curl aislado, utilizando Docker en Windows, sin afectar la estructura principal del repositorio BrainBash.

1. Prerrequisitos
Antes de comenzar, asegúrate de tener instalado:

Docker Desktop para Windows: Descargar aquí.

Nota: Durante la instalación, asegúrate de marcar la opción "Use WSL 2 instead of Hyper-V".

Abre Docker Desktop y verifica que el motor esté corriendo (icono verde).

2. Estructura de Directorios
Para mantener el entorno limpio y fuera del despliegue de producción, crearemos una carpeta docker separada. Tu proyecto debe quedar así:

Plaintext

BrainBash/             <-- Raíz del proyecto
├── .gitignore
├── install.sh
├── main.py
├── requirements.txt   
└── docker/            <-- CARPETA NUEVA (Entorno Local)
    ├── Dockerfile
    └── docker-compose.yml
3. Configuración de Archivos
Paso A: Ignorar la carpeta Docker en Git
Edita tu archivo .gitignore en la raíz (BrainBash/.gitignore) y agrega al final:

Plaintext

docker/
Paso B: docker/Dockerfile
Este archivo define la "receta" del sistema operativo. Copia y pega el siguiente contenido:

Dockerfile

# Usamos Python 3.11 sobre Debian "Bookworm" (estable, ligera y segura)
FROM python:3.11-slim-bookworm

# Evitamos archivos .pyc y logs en buffer para mejor depuración
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instalamos CURL (necesario para tu install.sh) y limpiamos caché
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Definimos el directorio de trabajo
WORKDIR /app

# Nota: El código no se copia aquí, se monta vía volumen.
Paso C: docker/docker-compose.yml
Este archivo orquesta el contenedor y conecta tu código. Copia y pega:

YAML

services:
  brainbash-dev:
    build: .
    container_name: brainbash_container
    volumes:
      # Mapea la carpeta PADRE (../) de Windows a la carpeta (/app) de Debian
      - ../:/app
    # Mantiene el contenedor encendido esperando tus comandos
    command: tail -f /dev/null
4. Uso del Entorno
Abre tu terminal (PowerShell o CMD) y navega a la carpeta de configuración:

PowerShell

cd Ruta\A\Tu\Proyecto\BrainBash\docker
1. Iniciar el entorno
Esto descarga Debian, construye la imagen y arranca el contenedor en segundo plano.

PowerShell

docker compose up -d
2. Entrar a la terminal (Debian)
Para ejecutar comandos dentro de la máquina virtual ligera:

PowerShell

docker compose exec brainbash-dev bash
Una vez dentro (verás el prompt root@...:/app#), puedes trabajar como si estuvieras en un servidor Linux.

5. Comandos de Prueba (Dentro del contenedor)
Una vez dentro de la terminal de Docker:

Instalar dependencias Python:

Bash

pip install -r requirements.txt
Correr tu aplicación:

Bash

python main.py
Probar el script de despliegue (install.sh):

Bash

chmod +x install.sh
./install.sh
Nota: Cualquier cambio que guardes en tus archivos en Windows (usando VS Code, Notepad, etc.) se reflejará instantáneamente dentro del contenedor.

6. Detener el Entorno
Cuando termines tu sesión de desarrollo, ejecuta lo siguiente desde tu PowerShell en la carpeta docker:

PowerShell

docker compose down
Esto detendrá y eliminará el contenedor, liberando memoria y CPU de tu máquina.