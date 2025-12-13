#!/usr/bin/env python3
import sys
import os
import argparse
from pathlib import Path

# Importaciones de nuestros modulos
from src.managers import DebianManager, AlpineManager, FedoraManager
from src.utils import Logger, Colors, TUI
from src.dotfiles import DotfileManager

# ==========================================
# CONFIGURACION
# ==========================================

BASE_PACKAGES = [
    "git",
    "zsh",
    "curl",
    "fzf",
    "bat",
    "python-dev"
]

DOTFILES_MAP = {
    "zshrc": ".zshrc",
    "kitty.conf": ".config/kitty/kitty.conf",
    "starship.toml": ".config/starship.toml"
}

# ==========================================
# LOGICA PRINCIPAL
# ==========================================

def get_distro_manager():
    """
    Lee /etc/os-release para determinar la distribucion
    y retorna la clase Manager correspondiente.
    """
    try:
        with open("/etc/os-release") as f:
            os_info = f.read().lower()
            
        if "alpine" in os_info:
            return AlpineManager("alpine")
        elif "fedora" in os_info or "rhel" in os_info or "centos" in os_info:
            return FedoraManager("fedora")
        elif "debian" in os_info or "ubuntu" in os_info or "kali" in os_info:
            distro_id = "ubuntu" if "ubuntu" in os_info else "debian"
            return DebianManager(distro_id)
        else:
            print("[Error] Distribucion no soportada automaticamente.")
            sys.exit(1)
            
    except FileNotFoundError:
        print("[Error] No se pudo leer /etc/os-release.")
        sys.exit(1)

def parse_arguments():
    """Define y captura los argumentos de linea de comandos para modo desatendido"""
    parser = argparse.ArgumentParser(description="Despliegue automatico de entorno Linux")
    parser.add_argument("--all", action="store_true", help="Instalar todo (Paquetes + Dotfiles) sin preguntar")
    parser.add_argument("--packages", action="store_true", help="Instalar solo paquetes")
    parser.add_argument("--dotfiles", action="store_true", help="Instalar solo dotfiles")
    parser.add_argument("--theme", type=str, default="blue", choices=["blue", "green", "magenta", "red"], help="Color del tema para logs (solo modo desatendido)")
    return parser.parse_args()

def main():
    # Capturamos argumentos
    args = parse_arguments()
    
    manager = get_distro_manager()

    # Mapa de colores para el modo desatendido
    theme_map = {
        "blue": Colors.BLUE,
        "green": Colors.GREEN,
        "magenta": Colors.MAGENTA,
        "red": Colors.RED
    }

    # ==============================================================================
    # RAMA A: MODO DESATENDIDO (CI/CD - Docker)
    # Se activa si se pasa alguno de los flags: --all, --packages, --dotfiles
    # ==============================================================================
    if args.all or args.packages or args.dotfiles:
        # Inicializamos logger directamente con el tema elegido (o default blue)
        logger = Logger(theme_color=theme_map[args.theme])
        logger.step("INICIANDO MODO DESATENDIDO")
        logger.info(f"Sistema detectado: {manager.__class__.__name__}")

        # --- Tarea 1: Paquetes ---
        if args.all or args.packages:
            logger.step("Fase 1: Gestion de Paquetes")
            try:
                manager.update()
                manager.install(BASE_PACKAGES)
                logger.success("Paquetes instalados.")
            except Exception as e:
                logger.error(f"Error instalando paquetes: {e}")
                sys.exit(1)

        # --- Tarea 2: Dotfiles ---
        if args.all or args.dotfiles:
            logger.step("Fase 2: Enlazando Dotfiles")
            repo_root = Path(os.getcwd())
            home_root = Path.home()
            dot_manager = DotfileManager(repo_root, home_root)
            
            for src, dest in DOTFILES_MAP.items():
                dot_manager.link(f"config/{src}", dest)
            logger.success("Dotfiles enlazados.")

        logger.success("Ejecucion desatendida finalizada.")
        sys.exit(0) # Salimos aquí para no mostrar el menú interactivo

    # ==============================================================================
    # RAMA B: MODO INTERACTIVO (Usuario Humano)
    # Se ejecuta si NO se pasaron argumentos
    # ==============================================================================
    
    tui = TUI()
    Colors.preview_all()
    
    theme_options = [
        (Colors.BLUE, "Azul (Estilo Debian)"),
        (Colors.GREEN, "Verde (Hacker)"),
        (Colors.MAGENTA, "Magenta (Cyberpunk)"),
        (Colors.RED, "Rojo (Alerta)")
    ]
    
    selected_color = tui.show_menu(
        "Configuracion Visual",
        "Selecciona el color base para los logs:",
        theme_options
    )
    
    logger = Logger(theme_color=selected_color)
    logger.step("INICIANDO DESPLIEGUE INTERACTIVO")
    logger.info(f"Sistema detectado. Usando gestor: {manager.__class__.__name__}")

    actions = [
        ("full", "Instalacion Completa (Paquetes + Dotfiles)"),
        ("pkgs", "Solo instalar Paquetes"),
        ("dots", "Solo enlazar Dotfiles (Config)"),
        ("exit", "Salir")
    ]

    action = tui.show_menu(
        "Menu Principal",
        "Que deseas hacer hoy?",
        actions
    )

    if action == "exit":
        sys.exit(0)

    # Ejecucion de Tareas Interactivas
    if action in ["full", "pkgs"]:
        logger.step("Fase 1: Gestion de Paquetes")
        try:
            manager.update()
            manager.install(BASE_PACKAGES)
            logger.success("Paquetes instalados correctamente.")
        except Exception as e:
            logger.error(f"Fallo en la instalacion de paquetes: {e}")
            sys.exit(1)

    if action in ["full", "dots"]:
        logger.step("Fase 2: Enlazando Dotfiles")
        repo_root = Path(os.getcwd())
        home_root = Path.home()
        dot_manager = DotfileManager(repo_root, home_root)
        
        for src, dest in DOTFILES_MAP.items():
            dot_manager.link(f"config/{src}", dest)   
        logger.success("Enlaces simbolicos creados.")

    logger.step("DESPLIEGUE FINALIZADO")
    logger.info("Reinicia tu terminal o ejecuta 'zsh' para ver los cambios.")

if __name__ == "__main__":
    # Verificacion de sistema (Solo corre en Linux/Mac)
    if hasattr(os, "geteuid"): 
        if os.geteuid() == 0: # type: ignore
            print("[Warn] Estas ejecutando como root. Es recomendable usar usuario normal con sudo.")
        
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Interrumpido por el usuario.")
        sys.exit(0)