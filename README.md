# WEAPONIZER PRO

O **WEAPONIZER PRO** é um framework avançado de engenharia reversa e
weaponization para aplicativos Android (APK). Esta edição especial "Red"
foi projetada para oferecer uma interface moderna, agressiva e um motor
de compatibilidade universal.

**Desenvolvedor:** Romildo (thuf)

------------------------------------------------------------------------
![Uploading image.png…]()


## 1. Visão Geral

O framework automatiza o ciclo completo de análise ofensiva de APKs. Ele
resolve dependências de forma autônoma, realiza auditorias estáticas em
busca de falhas de segurança e permite a reconstrução total do app com
assinaturas digitais válidas.

------------------------------------------------------------------------

## 2. Recursos Exclusivos

-   **Motor Universal de Bootstrap:** Suporte a múltiplos gerenciadores
    de pacotes (`APT`, `DNF`, `PACMAN`, `BREW`).
-   **Fail-Safe Manual:** Caso os repositórios do sistema falhem, o
    script realiza o download direto dos binários oficiais do
    **Apktool** (v2.9.3).
-   **Red Edition HUD:** Interface de comando estilizada em tons de
    vermelho e branco (Cyber-Red).
-   **Security Auditor:**
    -   Detecta Modo Debug ativado (Risco Crítico).
    -   Identifica configurações de rede que permitem interceptação de
        tráfego HTTPS (Bypass de SSL Pinning).
    -   Mapeia componentes exportados (Vulnerabilidades de Intent
        Injection).
-   **Re-Signature Engine:** Gera automaticamente chaves RSA de 2048
    bits para assinatura e selo de integridade.

------------------------------------------------------------------------

## 3. Requisitos e Instalação

-   **SO:** Linux (Qualquer distribuição) ou macOS.
-   **Python:** 3.x.
-   **Conexão:** Necessária apenas na primeira execução para baixar as
    ferramentas.

### Como Iniciar:

``` bash
python3 weaponizer.py
```

------------------------------------------------------------------------

## 4. Guia de Operação

### Opção 1: Reverse Engineering (Decompile & Scan)

-   **Função:** Extrai o código Smali, Manifesto e Recursos.
-   **Análise:** Realiza uma varredura automática por falhas de
    configuração.
-   **Saída:** Cria um diretório de projeto pronto para modificação
    manual.

### Opção 2: Payload Injection (Build & Sign)

-   **Função:** Recompila a pasta do projeto em um novo binário `.apk`.
-   **Assinatura:** Aplica assinaturas V2/V3 automaticamente.
-   **Resultado:** Gera um arquivo `_weaponized.apk` otimizado e pronto
    para instalação.

------------------------------------------------------------------------

## 5. Auditoria Técnica

O framework analisa proativamente: 1. **android:debuggable:** Essencial
para prevenir que atacantes conectem debuggers ao processo em tempo de
execução. 2. **Network Security Config:** Notifica se o desenvolvedor
permitiu certificados de usuário, o que viabiliza o uso de ferramentas
como Burp Suite e OWASP ZAP. 3. **Exported Components:** Lista portas de
entrada que podem ser exploradas para roubo de dados ou escalada de
privilégios via intents maliciosas.

------------------------------------------------------------------------

## 6. Aviso Legal

Este software é fornecido estritamente para fins de pesquisa de
segurança, auditoria e testes de penetração autorizados. O autor não se
responsabiliza por qualquer uso indevido, danos ou implicações legais
resultantes da utilização desta ferramenta em ambientes sem autorização
prévia por escrito.
