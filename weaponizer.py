import subprocess
import re
import os
import sys
import time
import urllib.request
from shutil import which

# Ativa o preenchimento automático com TAB
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
    exibir_banner()
    log("Iniciando rotina de conformidade do sistema...", "info")
    if not which("java"): install_package("openjdk-17-jdk")
    if not which("apktool"):
        if not install_package("apktool"): download_apktool_manual()
    if not which("zipalign") or not which("apksigner"): install_package("apksigner zipalign")

def install_package(pkg_name):
    for mgr in ["apt-get", "dnf", "pacman", "brew"]:
        if which(mgr):
            prefix = ["sudo"] if os.getuid() != 0 and mgr != "brew" else []
            try:
                subprocess.run(prefix + [mgr, "install", "-y", pkg_name], capture_output=True)
                return True
            except: continue
    return False

def download_apktool_manual():
    urls = {"wrapper": "https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool", "jar": "https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.9.3.jar"}
    target_bin = "/usr/local/bin"
    if not os.access(target_bin, os.W_OK): target_bin = os.path.expanduser("~/.local/bin")
    os.makedirs(target_bin, exist_ok=True)
    urllib.request.urlretrieve(urls["wrapper"], os.path.join(target_bin, "apktool"))
    urllib.request.urlretrieve(urls["jar"], os.path.join(target_bin, "apktool.jar"))
    subprocess.run(["chmod", "+x", os.path.join(target_bin, "apktool")])

def preparar_injecao(folder):
    """Módulo para orientar e preparar a injeção do payload."""
    log(f"Preparando Módulo de Injeção em: {folder}", "info")
    manifest_path = os.path.join(folder, "AndroidManifest.xml")
    
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            content = f.read()
            # Identifica a MainActivity (Ponto de entrada do App)
            main_activity = re.search(r'<activity [^>]*android:name="([^"]+)"', content)
            if main_activity:
                target = main_activity.group(1)
                print(f"\n{YELLOW}[!] PONTO DE HOOK IDENTIFICADO:{RESET}")
                print(f"    » Classe: {target}")
                print(f"    » Caminho: {folder}/smali/{target.replace('.', '/')}.smali")
                print(f"\n{WHITE}[*] Procedimento Recomendado:{RESET}")
                print(f"    1. Insira seu código payload .smali em: {folder}/smali/")
                print(f"    2. Adicione a chamada do payload no método 'onCreate' da classe acima.")
                print(f"    3. Use a Opção 2 do menu para recompilar e assinar.")
            else:
                log("Não foi possível identificar a MainActivity automaticamente.", "error")
    input(f"\n{YELLOW}Pressione Enter para confirmar autorização e voltar...{RESET}")

def build_e_assinar(out):
    signer = which("apksigner") or which("jarsigner")
    if not signer: return
    log(f"Build: Recompilando {out}...", "info")
    res = subprocess.run(["apktool", "b", out, "-o", "tmp.apk"], capture_output=True)
    if res.returncode != 0:
        log("Erro de compilação. Verifique os arquivos injetados.", "error"); return
    
    ks = "debug.keystore"
    if not os.path.exists(ks):
        subprocess.run(["keytool", "-genkey", "-v", "-keystore", ks, "-alias", "dev", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", "-storepass", "android", "-keypass", "android", "-dname", "CN=Weaponizer"], capture_output=True)
    
    log("Signing: Aplicando selo de integridade...", "info")
    subprocess.run(["apksigner", "sign", "--ks", ks, "--ks-pass", "pass:android", "--out", f"{out}_weaponized.apk", "tmp.apk"] if "apksigner" in signer else ["jarsigner", "-keystore", ks, "-storepass", "android", "tmp.apk", "dev"])
    if os.path.exists("tmp.apk"): os.remove("tmp.apk")
    log(f"Processo Concluído! Arquivo gerado: {out}_weaponized.apk", "success"); time.sleep(2)

def main():
    bootstrap()
    while True:
        exibir_banner()
        print(f" {BOLD}OPERATIONAL MENU:{RESET}")
        print(f" [{RED}1{RESET}] Reverse Engineering (Decompile & Scan)")
        print(f" [{RED}2{RESET}] Payload Injection (Build & Sign)")
        print(f" [{RED}3{RESET}] Terminar sessão")
        
        try: login = os.getlogin()
        except: login = "user"
        op = input(f"\n {BOLD}{RED}WEAPONIZER@{login}:~# {RESET}").strip()
        
        if op.lower() == "ls":
            print(f"\n{BOLD}{WHITE}Listagem de diretório:{RESET}")
            subprocess.run(["ls", "-F", "--color=auto"])
            input(f"\n{YELLOW}Pressione Enter para voltar ao menu...{RESET}")
            continue

        if op == "1":
            path = os.path.abspath(os.path.expanduser(input(f" {RED}»{RESET} Alvo (.apk): ").strip()))
            if os.path.exists(path):
                out = os.path.splitext(os.path.basename(path))[0]
                log(f"Extraindo dados de {os.path.basename(path)}...", "info")
                subprocess.run(["apktool", "d", path, "-o", out, "-f"], capture_output=True)
                # Chama a preparação de injeção logo após descompilar
                preparar_injecao(out)
            else: log("Arquivo não encontrado.", "error"); time.sleep(2)
        elif op == "2":
            out = input(f" {RED}»{RESET} Pasta do projeto: ").strip().rstrip('/')
            if os.path.isdir(out): build_e_assinar(out)
            else: log("Diretório inexistente.", "error"); time.sleep(2)
        elif op == "3": break
        elif op.lower() == "clear": continue
        else:
            if op != "": log(f"Comando '{op}' inválido.", "error"); time.sleep(1)

if __name__ == "__main__":
    main()
