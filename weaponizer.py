import subprocess
import re
import os
import sys
import time
import urllib.request
from shutil import which

# Ativa o preenchimento automático com TAB (Comum em sistemas Linux/macOS)
try:
    import readline
    readline.parse_and_bind("tab: complete")
except ImportError:
    pass

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
    """Exibe o banner corrigido com Raw String para não desalinhar."""
    os.system('clear' if os.name == 'posix' else 'cls')
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
    """.strip()
    print(banner)

def bootstrap():
    """Verifica e instala dependências de forma universal."""
    exibir_banner()
    log("Verificando ambiente operacional...", "info")
    
    if not which("java"): 
        log("Instalando Java...", "warn")
        install_package("openjdk-17-jdk")
    
    if not which("apktool"):
        log("Apktool não encontrado. Tentando instalação...", "warn")
        if not install_package("apktool"):
            download_apktool_manual()
            
    if not which("zipalign") or not which("apksigner"):
        log("Build-tools ausentes. Instalando...", "warn")
        install_package("apksigner zipalign")

def install_package(pkg_name):
    """Tenta usar o gerenciador de pacotes do sistema."""
    managers = ["apt-get", "dnf", "pacman", "brew"]
    for mgr in managers:
        if which(mgr):
            prefix = ["sudo"] if os.getuid() != 0 and mgr != "brew" else []
            cmd = prefix + [mgr, "install", "-y", pkg_name] if "pacman" not in mgr else prefix + ["pacman", "-S", "--noconfirm", pkg_name]
            try:
                subprocess.run(cmd, capture_output=True)
                return True
            except: continue
    return False

def download_apktool_manual():
    """Plano B: Baixa o apktool diretamente se o gerenciador falhar."""
    urls = {
        "wrapper": "https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool",
        "jar": "https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.9.3.jar"
    }
    target_bin = "/usr/local/bin"
    try:
        if not os.access(target_bin, os.W_OK):
            target_bin = os.path.expanduser("~/.local/bin")
            os.makedirs(target_bin, exist_ok=True)
        urllib.request.urlretrieve(urls["wrapper"], os.path.join(target_bin, "apktool"))
        urllib.request.urlretrieve(urls["jar"], os.path.join(target_bin, "apktool.jar"))
        subprocess.run(["chmod", "+x", os.path.join(target_bin, "apktool")])
        log(f"Apktool instalado em {target_bin}", "success")
    except Exception as e:
        log(f"Erro no download: {e}", "error"); sys.exit(1)

def analise_apk(out):
    """Realiza análise rápida do arquivo Manifesto."""
    manifest = os.path.join(out, "AndroidManifest.xml")
    if os.path.exists(manifest):
        print(f"\n{BOLD}{WHITE}[ AUDITORIA ESTÁTICA ]{RESET}")
        with open(manifest, "r", errors="ignore") as f:
            data = f.read()
            if 'android:debuggable="true"' in data:
                print(f"  {RED}»{RESET} MODO DEBUG ATIVADO (Risco Crítico)")
            if 'android:networkSecurityConfig' in data:
                print(f"  {YELLOW}»{RESET} Network Security Config detectado (Bypass de SSL)")
            if 'android:exported="true"' in data:
                print(f"  {WHITE}»{RESET} Componentes Externos Expostos")

def build_e_assinar(out):
    """Recompila e assina o APK."""
    signer = which("apksigner") or which("jarsigner")
    if not signer:
        log("Nenhum assinador encontrado!", "error"); return

    final_apk = f"{out}_weaponized.apk"
    log(f"Compilando diretório: {out}...", "info")
    subprocess.run(["apktool", "b", out, "-o", "tmp.apk"], capture_output=True)

    if not os.path.exists("debug.keystore"):
        log("Gerando nova Keystore...", "info")
        subprocess.run(["keytool", "-genkey", "-v", "-keystore", "debug.keystore", "-alias", "dev", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", "-storepass", "android", "-keypass", "android", "-dname", "CN=Weaponizer"], capture_output=True)

    log("Assinando artefato...", "info")
    if "apksigner" in signer:
        subprocess.run(["apksigner", "sign", "--ks", "debug.keystore", "--ks-pass", "pass:android", "--out", final_apk, "tmp.apk"])
    else:
        subprocess.run(["jarsigner", "-keystore", "debug.keystore", "-storepass", "android", "tmp.apk", "dev"])
        os.rename("tmp.apk", final_apk)
    
    if os.path.exists("tmp.apk"): os.remove("tmp.apk")
    log(f"Concluído: {final_apk}", "success"); time.sleep(2)

def main():
    bootstrap()
    while True:
        exibir_banner()
        print(f" {BOLD}OPERATIONAL MENU:{RESET}")
        print(f" [{RED}1{RESET}] Engenharia Reversa (Decompile & Scan)")
        print(f" [{RED}2{RESET}] Injetar Payload (Build & Sign)")
        print(f" [{RED}3{RESET}] Terminar sessão")
        
        try: user_login = os.getlogin()
        except: user_login = "root"

        op = input(f"\n {BOLD}{RED}WEAPONIZER@{user_login}:~# {RESET}").strip()
        
        # Comandos de Terminal
        if op.lower() == "ls":
            print(f"\n{BOLD}{WHITE}Listagem de diretório:{RESET}")
            subprocess.run(["ls", "-F", "--color=auto"])
            input(f"\n{YELLOW}Pressione Enter para voltar ao menu...{RESET}")
            continue
        elif op.lower() == "clear":
            continue

        # Opções do Menu
        if op == "1":
            raw_path = input(f" {RED}»{RESET} Alvo (.apk): ").strip()
            path = os.path.abspath(os.path.expanduser(raw_path))
            if os.path.exists(path):
                out = os.path.splitext(os.path.basename(path))[0]
                log(f"Extraindo dados de {os.path.basename(path)}...", "info")
                subprocess.run(["apktool", "d", path, "-o", out, "-f"], capture_output=True)
                analise_apk(out)
                log(f"Pasta de trabalho criada: {out}", "success")
                input("\nPresione Enter para retornar...")
            else: log("Arquivo não encontrado.", "error"); time.sleep(2)
            
        elif op == "2":
            out = input(f" {RED}»{RESET} Pasta do projeto: ").strip().rstrip('/')
            if os.path.isdir(out):
                build_e_assinar(out)
            else:
                log(f"Diretório '{out}' não encontrado.", "error")
                time.sleep(2)
                
        elif op == "3":
            log("Saindo do Framework...", "info"); break
        elif op == "": continue
        else:
            log(f"Comando ou opção '{op}' inválida.", "error"); time.sleep(1)

if __name__ == "__main__":
    main()
