# 📱 Thuf-Weaponizer - Documentação Oficial

O **APK Pentest Framework PRO** é uma solução completa para automação de
engenharia reversa, análise de segurança e modificação de aplicativos
Android. Este framework foi desenvolvido para centralizar tarefas
complexas em um ambiente interativo e profissional.

**Autor:** Romildo (thuf)

------------------------------------------------------------------------

## 📑 1. Visão Geral

O script atua como um orquestrador de ferramentas de segurança,
permitindo que o usuário descompile um APK, realize análises estáticas
profundas à procura de vulnerabilidades e segredos, injete modificações
e, por fim, reconstrua e assine o aplicativo para instalação.

------------------------------------------------------------------------

## 🚀 2. Recursos Principais

-   **Auto-Bootstrap (Auto-Instalação):** Na primeira execução, o script
    verifica se ferramentas como `apktool`, `java`, `zipalign` e
    `apksigner` estão presentes. Caso não estejam, ele realiza a
    instalação automática via gerenciador de pacotes `apt`.
-   **Análise de Integridade Forense:** Geração automática de Hashes MD5
    e SHA-256 para documentação e verificação de arquivos.
-   **Scanner de Vulnerabilidades Estático:**
    -   Identifica se o APK é depurável (`android:debuggable="true"`).
    -   Detecta configurações de segurança de rede que facilitam ataques
        Man-in-the-Middle (MITM).
    -   Lista componentes exportados que podem sofrer ataques de Intent
        Injection.
-   **Busca por Hardcoded Secrets (Segredos expostos):** Varredura
    inteligente em busca de chaves de API (Google, Firebase, AWS) e
    tokens de autenticação dentro do código Smali e arquivos de
    recursos.
-   **Build & Sign (Weaponization):**
    -   Recompila a estrutura de pastas em um novo binário.
    -   Aplica assinaturas digitais (Esquema V2/V3) essenciais para
        versões recentes do Android (11+).
    -   Gerencia automaticamente a criação de chaves (Keystores) de
        laboratório.

------------------------------------------------------------------------

## 🛠 3. Instalação e Requisitos

-   **Sistema Recomendado:** Kali Linux, Parrot Security, Ubuntu ou
    Debian.
-   **Python:** Versão 3.x instalada.
-   **Permissões de Admin:** É necessário acesso `sudo` apenas durante a
    execução inicial para a auto-instalação das ferramentas de sistema.

------------------------------------------------------------------------

## 💻 4. Guia de Uso Interativo

### Passo 1: Inicialização

Execute o script no terminal:

``` bash
python3 Thuf-Weaponizer.py
```

### Passo 2: Descompilação e Reconhecimento (Opção 1)

1.  Informe o caminho do seu arquivo `.apk`.
2.  O script exibirá as características de integridade do arquivo.
3.  Após a descompilação, verifique a saída do terminal; o script
    apresentará alertas automáticos sobre falhas de segurança
    encontradas no código-fonte e no manifesto.

### Passo 3: Modificação (Manual)

1.  Navegue até a pasta criada pelo script (mesmo nome do APK).
2.  Realize as alterações necessárias nos arquivos `.smali` ou no
    `AndroidManifest.xml`.

### Passo 4: Build e Assinatura (Opção 2)

1.  Escolha a opção 2 no menu principal.
2.  Digite o nome da pasta do projeto que você editou.
3.  O script irá gerar um arquivo final chamado
    `nome_da_pasta_modified_signed.apk`, devidamente alinhado e pronto
    para ser instalado no dispositivo de teste.

------------------------------------------------------------------------

## 🔍 5. Análise Técnica de Segurança

O framework realiza buscas automatizadas por: - **Firebase/Google API
Keys:** Detecta chaves que podem permitir acesso não autorizado a bancos
de dados na nuvem. - **AWS Credentials:** Procura por chaves de acesso e
segredos do ecossistema Amazon. - **Network Security Config:** Indica se
o app permite a instalação de certificados de confiança de usuário,
facilitando o uso de Proxies como Burp Suite.

------------------------------------------------------------------------

## ⚠️ 6. Aviso Legal

Esta ferramenta deve ser utilizada exclusivamente por profissionais de
segurança e pesquisadores em ambientes controlados e em ativos para os
quais possuem autorização explícita de teste. O autor não se
responsabiliza por danos, uso indevido ou consequências legais
resultantes do uso desta ferramenta para fins não éticos.
