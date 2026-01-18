import subprocess
import re
import os
import sys
import hashlib
from shutil import which

# --- CONFIGURAÇÕES DE INTERFACE ---
C_GREEN, C_YELLOW, C_RED, C_BLUE, C_BOLD, C_RESET = "\033[92m", "\033[93m", "\033[91m", "\033[94m", "\033[1m", "\033[0m"

def log(msg, level="info"):
    prefixes = {"info": f"{C_BLUE}[*]{C_RESET}", "success": f"{C_GREEN}[+]{C_RESET}", "warn": f"{C_YELLOW}[!]{C_RESET}", "error": f"{C_RED}[-]{C_RESET}"}
    print(f"{prefixes.get(level, '[*]')} {msg}")

# --- SISTEMA DE AUTO-INSTALAÇÃO ---

def instalar_dependencias():
    """Tenta instalar as dependências sistêmicas caso faltem."""
    log("Iniciando verificação de dependências para instalação...", "info")
    
    # Lista de pacotes necessários (Nome no sistema : Comando para testar)
    deps = {
        "openjdk-17-jdk": "java",
        "apktool": "apktool",
        "zipalign": "zipalign",
        "apksigner": "apksigner"
    }
    
    faltantes = []
    for pkg, cmd in deps.items():
        if not which(cmd):
            faltantes.append(pkg)
    
    if faltantes:
        log(f"As seguintes ferramentas estão faltando: {', '.join(faltantes)}", "warn")
        confirm = input(f"{C_BOLD}[?] Deseja tentar instalá-las automaticamente? (s/n): {C_RESET}").lower()
        
        if confirm == 's':
            try:
                log("Atualizando repositórios (isso pode pedir senha)...", "info")
                subprocess.run(["sudo", "apt-get", "update", "-y"], check=True)
                
                for pkg in faltantes:
                    log(f"Instalando {pkg}...", "info")
                    subprocess.run(["sudo", "apt-get", "install", "-y", pkg], check=True)
                
                log("Dependências instaladas com sucesso!", "success")
            except Exception as e:
                log(f"Falha na instalação automática: {e}", "error")
                log("Por favor, instale manualmente usando: sudo apt install " + " ".join(faltantes), "info")
        else:
            log("Procedendo sem instalar. O script pode falhar.", "warn")

    # Verifica dependência de biblioteca Python (pyfiglet)
    try:
        import pyfiglet
    except ImportError:
        log("Biblioteca 'pyfiglet' não encontrada. Instalando via pip...", "info")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyfiglet"], check=True)

# --- FUNÇÕES CORE (MANTIDAS E REFINADAS) ---

def check_env():
    """Retorna ferramenta de assinatura disponível."""
    if is_tool_installed("apksigner"): return "apksigner"
    return "jarsigner" if is_tool_installed("jarsigner") else None

def is_tool_installed(name):
    return which(name) is not None

def analise_apk(out):
    """Análise estática simplificada integrada."""
    manifest = os.path.join(out, "AndroidManifest.xml")
    if os.path.exists(manifest):
        with open(manifest, "r", errors="ignore") as f:
            data = f.read()
            if 'android:debuggable="true"' in data:
                log("ALERTA: O APK permite depuração (debuggable=true)!", "error")
            if 'android:networkSecurityConfig' in data:
                log("Network Security Config detectado. Verifique res/xml.", "warn")

def build_e_assinar(out, signer):
    """Ciclo de montagem e assinatura."""
    final_apk = f"{out}_signed.apk"
    tmp_apk = "tmp_build.apk"
    
    log(f"Compilando pasta {out}...", "info")
    res = subprocess.run(["apktool", "b", out, "-o", tmp_apk], capture_output=True, text=True)
    
    if res.returncode != 0:
        log(f"Erro na compilação:\n{res.stderr}", "error")
        return

    # Geração de Key se não existir
    if not os.path.exists("debug.keystore"):
        log("Gerando chave para assinatura técnica...", "info")
        subprocess.run(["keytool", "-genkey", "-v", "-keystore", "debug.keystore", "-alias", "android", 
                        "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", 
                        "-storepass", "android", "-keypass", "android", "-dname", "CN=Android, O=Google"], capture_output=True)

    # Assinatura
    log(f"Assinando APK com {signer}...", "info")
    if signer == "apksigner":
        subprocess.run(["apksigner", "sign", "--ks", "debug.keystore", "--ks-pass", "pass:android", "--out", final_apk, tmp_apk])
    else:
        subprocess.run(["jarsigner", "-keystore", "debug.keystore", "-storepass", "android", tmp_apk, "android"])
        os.rename(tmp_apk, final_apk)
    
    if os.path.exists(tmp_apk): os.remove(tmp_apk)
    log(f"Pronto: {final_apk}", "success")

# --- FLUXO PRINCIPAL ---

def main():
    # 1. Verificação e Instalação (Boot)
    instalar_dependencias()
    
    signer = check_env()
    
    # 2. Banner
    print(f"\n{C_BOLD}{C_BLUE}======================================{C_RESET}")
    try:
        import pyfiglet
        print(f"{C_GREEN}{pyfiglet.figlet_format('APK FRAMEWORK')}{C_RESET}")
    except:
        print(f"{C_GREEN}{C_BOLD}      APK FRAMEWORK PRO{C_RESET}")
    print(f"Nome: Romildo (thuf)    Site: helptecinfo.com")
    print(f"{C_BOLD}{C_BLUE}======================================{C_RESET}\n")

    while True:
        print(f"{C_BOLD}OPÇÕES:{C_RESET}")
        print("1. Descompilar e Analisar APK")
        print("2. Recompilar e Assinar (Weaponize)")
        print("3. Sair")
        
        op = input(f"\n{C_BOLD}Selecione > {C_RESET}").strip()

        if op == "1":
            path = input(f"{C_BLUE}[?] Caminho do APK: {C_RESET}").strip()
            if os.path.exists(path):
                out = os.path.splitext(os.path.basename(path))[0]
                subprocess.run(["apktool", "d", path, "-o", out, "-f"])
                analise_apk(out)
                log(f"Pasta de trabalho pronta: {out}", "success")
            else: log("Arquivo não encontrado.", "error")

        elif op == "2":
            out = input(f"{C_BLUE}[?] Nome da pasta descompilada: {C_RESET}").strip()
            if os.path.isdir(out):
                build_e_assinar(out, signer)
            else: log("Pasta inválida.", "error")

        elif op == "3":
            log("Saindo...", "info")
            break

if __name__ == "__main__":
    main()
