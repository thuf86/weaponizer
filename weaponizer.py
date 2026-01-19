import subprocess
import re
import os
import sys
import time
import urllib.request
from shutil import which

# --- PALETA DE CORES MODERNA ---
RED = "\33[91m"
DARK_RED = "\33[31m"
WHITE = "\33[97m"
BOLD = "\33[1m"
RESET = "\33[0m"
YELLOW = "\33[93m"

def log(msg, level="info"):
    p = {"info": f"{WHITE}[*]{RESET}", "success": f"{RED}[+]{RESET}", "warn": f"{YELLOW}[!]{RESET}", "error": f"{BOLD}{RED}[-]{RESET}"}
    print(f"{p.get(level, '[*]')} {msg}")

def exibir_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    
    # Adicionamos 'fr' antes das aspas para ser uma Raw String Formatada
    banner = fr"""
{RED} ██╗    ██╗███████╗ █████╗ ██████╗  ██████╗ ███╗   ██╗██╗███████╗███████╗██████╗ 
{RED} ██║    ██║██╔════╝██╔══██╗██╔══██╗██╔═══██╗████╗  ██║██║╚══███╔╝██╔════╝██╔══██╗
{DARK_RED} ██║ █╗ ██║█████╗  ███████║██████╔╝██║   ██║██╔██╗ ██║██║  ███╔╝ █████╗  ██████╔╝
{DARK_RED} ██║███╗██║██╔══╝  ██╔══██║██╔═══╝ ██║   ██║██║╚██╗██║██║ ███╔╝  ██╔══╝  ██╔══██╗
{RED} ╚███╔███╔╝███████╗██║  ██║██║     ╚██████╔╝██║ ╚████║██║███████╗███████╗██║  ██║
{RED}  ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═══╝╚═╝╚══════╝╚══════╝╚═╝  ╚═╝
{RESET}
 {WHITE}{BOLD}WEAPONIZER PRO{RESET} | {WHITE}Dev: Romildo (thuf){RESET}
 {DARK_RED}─────────────────────────────────────────────────────────────────────────────{RESET}
    """.strip() # O .strip() remove espaços extras no topo e na base
    print(banner)

def bootstrap():
    exibir_banner()
    log("Iniciando rotina de conformidade do sistema...", "info")
    time.sleep(1)

    if not which("java"):
        log("Java Runtime não detectado no PATH.", "warn")
        install_package("openjdk-17-jdk")

    if not which("apktool"):
        log("Apktool ausente. Tentando resolver via repositórios...", "warn")
        if not install_package("apktool"):
            log("Repositórios falharam. Iniciando download dos binários oficiais...", "warn")
            download_apktool_manual()

    if not which("zipalign") or not which("apksigner"):
        log("Build-tools (zipalign/apksigner) ausentes.", "warn")
        install_package("apksigner zipalign")

def install_package(pkg_name):
    """Instalador multi-gerenciador."""
    managers = ["apt-get", "dnf", "pacman", "brew"]
    for mgr in managers:
        if which(mgr):
            log(f"Instalando {pkg_name} via {mgr}...", "info")
            prefix = ["sudo"] if os.getuid() != 0 and mgr != "brew" else []
            cmd = prefix + [mgr, "install", "-y", pkg_name] if "pacman" not in mgr else prefix + ["pacman", "-S", "--noconfirm", pkg_name]
            try:
                subprocess.run(cmd, capture_output=True)
                return True
            except: continue
    return False

def download_apktool_manual():
    """Garante o apktool em sistemas onde o APT falha."""
    urls = {
        "wrapper": "https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool",
        "jar": "https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.9.3.jar"
    }
    target_bin = "/usr/local/bin"
    try:
        if not os.access(target_bin, os.W_OK):
            target_bin = os.path.expanduser("~/.local/bin")
            os.makedirs(target_bin, exist_ok=True)
            log(f"Usando diretório local do usuário: {target_bin}", "info")
            
        log("Baixando script wrapper...", "info")
        urllib.request.urlretrieve(urls["wrapper"], os.path.join(target_bin, "apktool"))
        
        log("Baixando binário JAR v2.9.3...", "info")
        urllib.request.urlretrieve(urls["jar"], os.path.join(target_bin, "apktool.jar"))
        
        subprocess.run(["chmod", "+x", os.path.join(target_bin, "apktool")])
        log(f"Binários instalados em {target_bin}. Certifique-se que está no seu PATH.", "success")
    except Exception as e:
        log(f"Falha crítica no download: {e}", "error")
        sys.exit(1)

def build_e_assinar(out):
    signer = which("apksigner") or which("jarsigner")
    if not signer:
        log("Nenhuma ferramenta de assinatura disponível.", "error")
        return

    final = f"{out}_weaponized.apk"
    log(f"Recompilando diretório: {out}...", "info")
    subprocess.run(["apktool", "b", out, "-o", "tmp.apk"], capture_output=True)

    if not os.path.exists("debug.keystore"):
        log("Gerando nova Keystore de auditoria...", "info")
        subprocess.run(["keytool", "-genkey", "-v", "-keystore", "debug.keystore", "-alias", "dev", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", "-storepass", "android", "-keypass", "android", "-dname", "CN=Weaponizer"], capture_output=True)

    log("Aplicando assinatura e selo de integridade...", "info")
    if "apksigner" in signer:
        subprocess.run(["apksigner", "sign", "--ks", "debug.keystore", "--ks-pass", "pass:android", "--out", final, "tmp.apk"])
    else:
        subprocess.run(["jarsigner", "-keystore", "debug.keystore", "-storepass", "android", "tmp.apk", "dev"])
        os.rename("tmp.apk", final)

    if os.path.exists("tmp.apk"): os.remove(tmp_apk)
    log(f"Artefato concluído: {final}", "success")
    time.sleep(2)

def main():
    bootstrap()
    while True:
        exibir_banner()
        print(f" {BOLD}OPERATIONAL MENU:{RESET}")
        print(f" [{RED}1{RESET}] Engenharia Reversa (Decompile & Scan)")
        print(f" [{RED}2{RESET}] Injetar Payload (Build & Sign)")
        print(f" [{RED}3{RESET}] Terminar sessão")
        
        op = input(f"\n {BOLD}{RED}WEAPONIZER@{os.getlogin()}:~# {RESET}").strip()
        
        if op == "1":
            path = input(f" {RED}»{RESET} Alvo (.apk): ").strip()
            if os.path.exists(path):
                out = os.path.splitext(os.path.basename(path))[0]
                log(f"Extraindo dados de {path}...", "info")
                subprocess.run(["apktool", "d", path, "-o", out, "-f"], capture_output=True)
                log(f"Pasta de trabalho criada: {out}", "success")
                input("\nPressione Enter para retornar ao HUD...")
            else:
                log("Arquivo não localizado.", "error")
                time.sleep(2)
        elif op == "2":
            out = input(f" {RED}»{RESET} Pasta do projeto: ").strip()
            if os.path.isdir(out):
                build_e_assinar(out)
            else:
                log("Diretório inexistente.", "error")
                time.sleep(2)
        elif op == "3":
            log("Encerrando framework...", "info")
            break

if __name__ == "__main__":
    main()



