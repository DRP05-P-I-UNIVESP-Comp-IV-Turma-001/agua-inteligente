# 💧 Projeto Integrador IV — Água Inteligente

**Monitoramento de vazão em tempo real com FastAPI + Streamlit + Analytics**

![Arquitetura do Sistema Água Inteligente](docs/arquitetura_agua_inteligente.png)

Bem-vindo ao projeto da **Turma 001 – UNIVESP (Ciência de Dados)**!
Este sistema acompanha a **vazão de água em tempo real**, detecta **anomalias de consumo** e exibe tudo em um **dashboard web** intuitivo e fácil de usar.

O objetivo é permitir que **qualquer integrante do grupo** consiga rodar o sistema completo no próprio computador, **sem precisar configurar manualmente** o backend e o dashboard.
Para isso, criamos o **launcher.py**, que executa tudo automaticamente — e também pode ser transformado em um **executável (.exe)** pronto para uso.

---

## ✅ Pré-requisitos

Antes de começar, confirme que você tem no seu Windows:

* ✔ **VS Code** instalado
* ✔ **Python 3.10 ou superior** instalado
* ✔ **Conta no GitHub**
* ✔ **Conexão com a internet** 👍

---

## 🚀 Instalação rápida (para integrantes do grupo)

Siga os passos **nesta ordem**, sem pular nenhum!
Esses passos funcionam para todos os membros do grupo.

---

### 1️⃣ Baixar o projeto

Abra o **VS Code** → menu **Exibir > Terminal**
E digite:

```bash
git clone https://github.com/DRP05-P-I-UNIVESP-Comp-IV-Turma-001/agua-inteligente.git
cd agua-inteligente
```

---

### 2️⃣ Criar e ativar o ambiente virtual

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se aparecer erro de permissão, digite:

```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Depois, **ative novamente o ambiente virtual**.

---

### 3️⃣ Instalar as dependências

```bash
pip install -r requirements.txt
```

Esse comando baixa e instala todas as bibliotecas que o sistema precisa, como **FastAPI**, **Streamlit**, **Uvicorn**, **Pandas**, entre outras.

---

### 4️⃣ Rodar o sistema completo (modo fácil)

Depois que tudo estiver instalado, execute o **launcher.py**:

```bash
python launcher.py
```

O **launcher** faz tudo automaticamente:

1. Sobe o **backend FastAPI** (servidor de dados)
2. Aguarda o **/health** responder
3. Abre o **Dashboard Streamlit** no navegador
4. Exibe as informações de vazão e anomalias em tempo real

Se o navegador não abrir sozinho, acesse manualmente:
👉 [http://localhost:8501](http://localhost:8501)

---

## 🧩 Estrutura do projeto

```
agua_inteligente/
├─ edge/               # Simulador de sensores (gera dados de teste)
├─ ingestion/          # Backend FastAPI + Banco SQLite
│  └─ main.py
├─ analytics/          # Detecção de anomalias (Z-score e IQR)
│  ├─ processing.py
│  └─ test_processing.py
├─ dashboard/          # Interface Streamlit (gráficos e KPIs)
│  ├─ app.py
│  └─ config.py        # Configuração de API e fuso horário
├─ docs/               # Documentos, diagramas e prints
├─ launcher.py         # Script que inicia tudo automaticamente
├─ requirements.txt    # Lista de dependências
└─ .venv/              # Ambiente virtual (não precisa subir pro GitHub)
```

---

## 🧠 Como o módulo Analytics funciona

O sistema analisa o histórico de medições e detecta **padrões anormais** de vazão usando dois métodos:

* **Z-score (padrão)** → estável para séries regulares
* **IQR (Intervalo Interquartil)** → mais sensível a picos e variações bruscas

No dashboard, você pode ajustar:

* Tamanho da janela de análise
* Limiar de detecção (Z ou IQR)
* Número máximo de leituras exibidas

---

## 👨‍💻 Modo desenvolvedor (opcional)

Se quiser rodar os módulos separadamente:

### A) Backend (FastAPI)

```bash
uvicorn ingestion.main:app --reload
```

Verifique no navegador:

* `http://127.0.0.1:8000/health`
* `http://127.0.0.1:8000/readings`
* `http://127.0.0.1:8000/analytics/anomalies`

### B) Dashboard (Streamlit)

Em outro terminal:

```bash
streamlit run dashboard/app.py
```

Acesse: [http://localhost:8501](http://localhost:8501)

---

## ⚙️ Variáveis de ambiente opcionais

No PowerShell:

```powershell
$env:AGUA_API_BASE="http://127.0.0.1:8000"
$env:AGUA_TZ="America/Sao_Paulo"
```

O arquivo `dashboard/config.py` usa essas variáveis automaticamente:

```python
API_BASE = os.getenv("AGUA_API_BASE", "http://127.0.0.1:8000")
TIMEZONE = os.getenv("AGUA_TZ", "America/Sao_Paulo")
```

---

## 🌐 Acessar em outro dispositivo

O Streamlit mostra um endereço de rede, como:

```
Network URL: http://192.168.15.8:8501
```

Acesse esse link de outro dispositivo na **mesma rede Wi-Fi** para visualizar o painel remotamente.

---

## 🖥️ Criar o executável (.exe)

> Use este modo quando quiser que o sistema rode com **dois cliques**, sem precisar abrir o VS Code.

1️⃣ Instale o PyInstaller:

```bash
pip install pyinstaller
```

2️⃣ Gere o executável com:

```bash
pyinstaller -y .\AguaInteligente.spec
```

Esse comando cria o executável dentro da pasta `dist/`.

3️⃣ Para rodar:

* Abra o arquivo `dist/AguaInteligente.exe`
* Ele iniciará o backend e o dashboard automaticamente
* Se o navegador não abrir, acesse: [http://localhost:8501](http://localhost:8501)

🧠 *Importante:* Se o antivírus bloquear o `.exe`, use a opção “Permitir sempre” — é comum com executáveis gerados localmente.

---

## 🔍 O que aparece no Dashboard

* **Indicadores (KPIs)**: sensores ativos, total de leituras, média, pico e somatório
* **Gráfico temporal** da vazão
* **Alertas recentes** de anomalias
* **Status dos hidrômetros**:

  * 🔺 Vermelho → consumo fora do padrão
  * ✅ Verde → normal

---

## 🧾 Próximas etapas do projeto (Roadmap)

| Etapa                                           | Status               |
| ----------------------------------------------- | -------------------- |
| Dashboard básico com KPIs e gráficos            | ✅ Concluído          |
| Backend FastAPI com banco SQLite                | ✅ Concluído          |
| Detecção de anomalias (Z-score e IQR)           | ✅ Concluído          |
| Launcher automático e empacotamento `.exe`      | ✅ Concluído          |
| Métricas por setor e sazonalidade               | ⏳ Em desenvolvimento |
| Alertas visuais no gráfico                      | ⏳ Planejado          |
| Exportação de relatórios (CSV/PDF)              | ⏳ Planejado          |
| Integração com sensores reais no módulo `edge/` | ⏳ Planejado          |

---

## 🧯 Ajuda rápida

| Situação                           | O que fazer                                                                        |
| ---------------------------------- | ---------------------------------------------------------------------------------- |
| O painel não abre                  | Verifique se o backend responde em `/health`. O launcher faz isso automaticamente. |
| Erro de permissão ao ativar o venv | Use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.                  |
| A tabela está vazia                | Aguarde alguns segundos — o simulador de sensores vai gerar dados.                 |
| Erro no `.exe`                     | Verifique se o antivírus não bloqueou o arquivo.                                   |
| O `.exe` fecha sozinho             | Execute via PowerShell para ver a mensagem de erro.                                |

---

## 🤝 Equipe

* **Magno Bruno Camargo Proença**
* **Mauro Sergio Bouwman Leão**
* **Bruno Luiz Silva Marchi**
* **Beatriz Aiello Yazbek**

---

