# 💧 Projeto Integrador IV

## Água Inteligente — Monitoramento de Vazão em Tempo Real

Bem-vindo ao nosso projeto! Ele faz parte do **Curso de Ciência de Dados da UNIVESP – Turma 001**.
A ideia é acompanhar a **vazão da água em tempo real** utilizando um painel visual acessível no navegador.

Este arquivo explica **como qualquer integrante do grupo** pode instalar e rodar o sistema no próprio computador, mesmo que nunca tenha mexido com Git ou programação.

---

## ✅ O que você vai precisar antes de começar

Certifique-se de que no seu computador existe:

✔ VS Code instalado
✔ Python instalado
✔ Conta no GitHub (já criada)
✔ Internet funcionando 👍

Se tudo isso estiver ok, podemos começar.

---

## 🚀 Como instalar e rodar o projeto no seu computador

Siga com calma. Faça exatamente na ordem.

---

### 1️⃣ Baixar o projeto do GitHub

Abra o **VS Code**
Clique em:
`View (Exibir)` → `Terminal`

No terminal que abriu lá embaixo, copie e cole o comando abaixo e aperte **Enter**:

```bash
git clone https://github.com/DRP05-P-I-UNIVESP-Comp-IV-Turma-001/agua-inteligente.git
```

Esse comando **baixa o projeto para o seu computador**.

Depois, entre dentro da pasta do projeto:

```bash
cd agua-inteligente
```

---

### 2️⃣ Criar um “ambiente virtual”

Isso prepara o computador para rodar o projeto sem dar conflitos.

```bash
python -m venv .venv
```

Agora ative o ambiente:

```bash
.\.venv\Scripts\Activate.ps1
```

✅ Se der certo, você verá no terminal algo assim:
**(.venv)** no início da linha

> Se aparecer um erro dizendo que scripts estão bloqueados:
> Rode este comando e depois tente ativar novamente
>
> ```bash
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```

---

### 3️⃣ Instalar tudo o que o sistema precisa

```bash
pip install -r requirements.txt
```

Isso pode demorar um pouco. Aguarde até terminar.

---

### 4️⃣ Rodar o painel da água inteligente

Execute este comando:

```bash
streamlit run dashboard/app.py
```

Depois de alguns segundos irá abrir **automáticamente seu navegador** com o painel funcionando.

Se não abrir, entre neste link manualmente:

👉 [http://localhost:8501](http://localhost:8501)

---

## 🌐 Testar em outro dispositivo da casa

O terminal mostra também outro endereço chamado **Network URL**.
Ele permite abrir o painel usando **celular, tablet ou outro notebook**, desde que estejam na mesma rede Wi-Fi.

Exemplo:

👉 [http://192.168.15.8:8501](http://192.168.15.8:8501)

---

## 🤝 Equipe do Projeto

* [Magno Bruno Camargo Proença]
* [Mauro Sergio Bouwman Leão]
* [Bruno Luiz Silva Marchi]
* [Beatriz Aiello Yazbek]

---

## 🛠 Próximas etapas do desenvolvimento

✔ Criar painel inicial ✅
⬜ Incluir dados simulados de sensores
⬜ Atualização automática do gráfico em tempo real
⬜ API com FastAPI
⬜ Captura de dados reais (futuro)

---

## 💡 Ajuda rápida

| Situação                                   | O que fazer                                 |
| ------------------------------------------ | ------------------------------------------- |
| Nada acontece quando rodo o último comando | Confira se aparece **(.venv)** no terminal  |
| Abriu um erro estranho                     | Feche o VS Code e abra de novo              |
| Erro sobre permissionamento                | Rode o comando `Set-ExecutionPolicy…` acima |
| A página não abre                          | Copie o link e cole no navegador            |

Se nada der certo… me chama no grupo! 😅

---


