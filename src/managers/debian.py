import subprocess
import os
import shutil
import json
import urllib.request
import platform
from pathlib import Path
from typing import List
from ..core import PackageManager

class DebianManager(PackageManager):
    def update(self):
        print("[Debian] Actualizando sistema...")
        # Actualizamos la lista
        subprocess.run(["sudo", "apt", "update", "-qq"], check=True)
        # Actualizamos los paquetes instalados
        subprocess.run(["sudo", "apt", "upgrade", "-y"], check=True)

    def install(self, packages: List[str]):
        apt_packages = []
        manual_packages = []
        
        # Herramientas que instalamos manualmente desde GitHub
        modern_tools = ["eza", "bat", "htop", "fzf", "starship", "zoxide", "tldr"]

        for pkg in packages:
            mapped = self._get_mapped_name(pkg)
            if mapped in modern_tools or pkg in modern_tools:
                manual_packages.append(mapped)
            else:
                apt_packages.append(mapped)

        if apt_packages:
            extras = ["curl", "wget", "tar", "unzip"]
            to_install = list(set(apt_packages + extras))
            
            print(f"[APT] Instalando base: {', '.join(to_install)}")
            try:
                subprocess.run(["sudo", "apt", "install", "-y"] + to_install, check=True)
            except subprocess.CalledProcessError:
                print("[Error] Fallo APT. Revisa tu conexión.")

        for tool in manual_packages:
            self._install_binary(tool)

    def _get_arch_terms(self):
        arch = platform.machine().lower()
        if arch == "x86_64": return ["x86_64", "amd64"]
        if arch in ["aarch64", "arm64"]: return ["aarch64", "arm64"]
        return [arch]

    def _download_github_asset(self, repo, keyword, output_name, allow_musl=False):
        print(f"[GitHub] Buscando {output_name} en {repo}...")
        try:
            api_url = f"https://api.github.com/repos/{repo}/releases/latest"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'python'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
            
            arch_terms = self._get_arch_terms()
            download_url = None
            
            for asset in data["assets"]:
                name = asset["name"].lower()
                if "linux" not in name and "unknown-linux" not in name: continue
                if not any(term in name for term in arch_terms): continue
                if keyword and keyword not in name: continue
                if "musl" in name and not allow_musl: continue
                
                download_url = asset["browser_download_url"]
                break
            
            if not download_url:
                print(f"[Error] No binario compatible en {repo}")
                return False

            print(f"Descargando: {download_url}")
            subprocess.run(["curl", "-L", "-o", output_name, download_url], check=True)
            return True
        except Exception as e:
            print(f"[Error] Fallo descarga {output_name}: {e}")
            return False

    def _install_binary(self, tool):
        if shutil.which(tool):
            print(f"[Skip] {tool} ya está instalado.")
            return

        print(f"[Binario] Instalando {tool}...")
        original_cwd = os.getcwd() 
        temp_dir = Path("/tmp/brainbash_bin")
        if temp_dir.exists(): shutil.rmtree(temp_dir)
        temp_dir.mkdir(exist_ok=True)
        
        try:
            os.chdir(temp_dir)

            if tool == "eza":
                if self._download_github_asset("eza-community/eza", ".tar.gz", "eza.tar.gz"):
                    subprocess.run("tar -xzf eza.tar.gz", shell=True)
                    subprocess.run("sudo mv ./eza /usr/local/bin/", shell=True)
                    subprocess.run("sudo chmod +x /usr/local/bin/eza", shell=True)

            elif tool == "bat":
                if self._download_github_asset("sharkdp/bat", ".tar.gz", "bat.tar.gz"):
                    subprocess.run("tar -xzf bat.tar.gz", shell=True)
                    subprocess.run("sudo mv bat-*/bat /usr/local/bin/", shell=True)
                    subprocess.run("sudo chmod +x /usr/local/bin/bat", shell=True)

            elif tool == "fzf":
                if self._download_github_asset("junegunn/fzf", ".tar.gz", "fzf.tar.gz"):
                    subprocess.run("tar -xzf fzf.tar.gz", shell=True)
                    subprocess.run("sudo mv fzf /usr/local/bin/", shell=True)
                    subprocess.run("sudo chmod +x /usr/local/bin/fzf", shell=True)

            elif tool == "tldr":
                if self._download_github_asset("dbrgn/tealdeer", "linux", "tldr", allow_musl=True):
                    subprocess.run("chmod +x tldr", shell=True)
                    subprocess.run("sudo mv tldr /usr/local/bin/", shell=True)

            elif tool == "starship":
                # Instalador oficial a /usr/local/bin
                subprocess.run("curl -sS https://starship.rs/install.sh | sh -s -- -y", shell=True)
            
            elif tool == "zoxide":
                # FIX: Forzamos instalacion en /usr/local/bin para evitar problemas de PATH
                cmd = "curl -sS https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | sh -s -- --bin-dir /usr/local/bin"
                subprocess.run(cmd, shell=True)

            print(f"{tool} instalado.")

        except Exception as e:
            print(f"Error instalando {tool}: {e}")
        finally:
            os.chdir(original_cwd) 
            shutil.rmtree(temp_dir, ignore_errors=True)