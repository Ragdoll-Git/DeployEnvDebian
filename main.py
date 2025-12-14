#!/usr/bin/env python3
import sys
import os
import argparse
import subprocess
import time
from pathlib import Path

# Importaciones del proyecto
from src.managers import DebianManager, AlpineManager, FedoraManager
from src.utils import Logger, Colors, TUI
from src.dotfiles import DotfileManager

# ==========================================
# CONFIGURACION DE COMPONENTES
# ==========================================

MODELS_MAP = {
    "model_qwen": "qwen3:0.6b",         # Qwen 3 (0.6B)
    "model_gemma": "gemma3:1b",         # Gemma 3 (1B Instruct)
    "model_phi": "phi4:mini"            # Phi-4 Mini Instruct
}

# Grupos de paquetes
PKG_BASE = ["git", "curl", "zsh", "python-dev"]

PKG_MODERN = ["fzf", "bat", "eza", "btop", "tldr"] 
PKG_SHELL = ["zoxide", "starship"]

DOTFILES_MAP = {
    "zshrc": ".zshrc",
    "kitty.conf": ".config/kitty/kitty.conf",
    "starship.toml": ".config/starship.toml"
}

# ==========================================
# FUNCIONES DE SOPORTE
# ==========================================

def get_manager():
    """Detecta la distro y devuelve el gestor de paquetes adecuado"""
    try:
        with open("/etc/os-release") as f: data = f.read().lower()
        if "alpine" in data: return AlpineManager("alpine")
        if "fedora" in data: return FedoraManager("fedora")
        if "debian" in data or "ubuntu" in data: return DebianManager("debian")
    except Exception:
        pass
    print("Error: Sistema operativo no detectado.")
    sys.exit(1)

def install_omz(logger):
    """Instala Oh My Zsh si no existe"""
    if (Path.home() / ".oh-my-zsh").exists():
        logger.info("[Skip] Oh My Zsh ya instalado.")
        return
    
    logger.info("Descargando Oh My Zsh...")
    # Usamos --unattended para que no pida confirmación y bloquee el script
    cmd = 'sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended'
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logger.success("Oh My Zsh instalado.")

def setup_ollama(logger, selected_models):
    """Instala el motor Ollama y descarga los modelos pedidos"""
    # 1. Instalar Motor (si falta)
    if subprocess.run("command -v ollama", shell=True, stdout=subprocess.DEVNULL).returncode != 0:
        logger.step("Instalando Motor Ollama")
        subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True)
    else:
        logger.info("[Skip] Motor Ollama ya presente.")

    if not selected_models:
        return

    logger.info("Esperando que el servicio de IA inicie...")
    time.sleep(3) # Pausa técnica para asegurar que el daemon levante
    
    # 2. Descargar Modelos
    for menu_id in selected_models:
        ollama_tag = MODELS_MAP.get(menu_id)
        if ollama_tag:
            logger.step(f"IA: Descargando modelo {ollama_tag}")
            try:
                # check=False para que si falla uno (ej. mala conexión) no detenga todo el script
                ret = subprocess.run(f"ollama pull {ollama_tag}", shell=True)
                if ret.returncode == 0:
                    logger.success(f"Modelo {ollama_tag} listo.")
                else:
                    logger.error(f"Error al descargar {ollama_tag}.")
            except Exception as e:
                logger.error(f"Fallo critico en IA: {e}")

# ==========================================
# PUNTO DE ENTRADA PRINCIPAL
# ==========================================

def main():
    manager = get_manager()
    tui = TUI()

    # --- 1. CONFIGURACION VISUAL (Primer paso único) ---
    Colors.preview_all()
    theme_opts = [
        (Colors.BLUE, "Azul (Debian)"), 
        (Colors.GREEN, "Verde (Hacker)"),
        (Colors.MAGENTA, "Magenta (Cyberpunk)"), 
        (Colors.RED, "Rojo (Admin)")
    ]
    # Si TUI falla, usa Azul por defecto
    try:
        color = tui.show_menu("BrainBash", "Selecciona el color del instalador:", theme_opts)
    except:
        color = Colors.BLUE
        
    logger = Logger(color)

    # --- 2. MENU UNIFICADO (Checklist) ---
    # Formato: (ID, Descripcion, EstadoDefault ["ON"/"OFF"])
    menu_items = [
        ("sys_base",   "Paquetes Base (Git, Zsh, Python)", "ON"),
        ("sys_modern", "Modern CLI (Eza, Bat, htop)", "ON"),
        ("sys_omz",    "Shell (Oh My Zsh + Starship)", "ON"),
        ("dotfiles",   "Configs personalizadas", "ON"),
        ("ai_engine",  "Motor IA (Ollama)", "OFF"),
        ("model_qwen", "IA: Qwen 3 (0.6B) - Ultraligero (500MB RAM)", "OFF"),
        ("model_gemma","IA: Gemma 3 (1B) - Balanceado (1.5GB RAM)", "OFF"),
        ("model_phi",  "IA: Phi-4 (Mini) - Pesado (+4GB RAM)", "OFF")
    ]

    selection = tui.show_checklist(
        "Menu Principal", 
        "Espacio: Marcar/Desmarcar | Enter: Confirmar", 
        menu_items
    )

    if not selection:
        logger.info("No seleccionaste nada. Saliendo...")
        sys.exit(0)

    # --- 3. EJECUCION DE TAREAS ---
    
    # A) Instalación de Paquetes
    pkgs_to_install = []
    if "sys_base" in selection: pkgs_to_install.extend(PKG_BASE)
    if "sys_modern" in selection: pkgs_to_install.extend(PKG_MODERN)
    if "sys_omz" in selection: pkgs_to_install.extend(PKG_SHELL)

    if pkgs_to_install:
        logger.step("Fase 1: Paquetes del Sistema")
        try:
            manager.update()
            manager.install(pkgs_to_install)
            logger.success("Paquetes instalados.")
        except Exception as e:
            logger.error(f"Error en paquetes: {e}")
            # No salimos con sys.exit para intentar las siguientes fases

    # B) Configuración de Shell (OMZ)
    if "sys_omz" in selection:
        logger.step("Fase 2: Configuración Shell")
        install_omz(logger)

    # C) Enlace de Dotfiles
    if "dotfiles" in selection:
        logger.step("Fase 3: Dotfiles")
        
        # CORRECCION: Usar la ruta real del script, no el CWD del usuario
        # Esto asegura que encuentre la carpeta 'config' sin importar desde donde ejecutes
        repo_root = Path(__file__).parent.resolve()
        home_root = Path.home()
        
        dm = DotfileManager(repo_root, home_root)
        for src, dest in DOTFILES_MAP.items():
            dm.link(f"config/{src}", dest)
        logger.success("Enlaces creados.")

    # D) Inteligencia Artificial
    # Filtramos qué modelos eligió el usuario
    ai_models_selected = [x for x in selection if x.startswith("model_")]
    
    # Si eligió instalar el motor O algún modelo, ejecutamos la fase IA
    if "ai_engine" in selection or ai_models_selected:
        logger.step("Fase 4: Inteligencia Artificial")
        setup_ollama(logger, ai_models_selected)

    logger.step("INSTALACION FINALIZADA")
    logger.info("Por favor, reinicia tu terminal.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelado por usuario.")
        sys.exit(0)