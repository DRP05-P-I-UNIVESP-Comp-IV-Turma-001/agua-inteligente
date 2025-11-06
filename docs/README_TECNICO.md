# Documentação Técnica – Água Inteligente

## 1. Estrutura dos módulos
- edge → Simulador de sensores IoT
- ingestion → API FastAPI para ingestão de dados
- analytics → Algoritmos de detecção de anomalias
- dashboard → Interface interativa com Streamlit
- docs → Relatórios e documentação acadêmica

---

## 2. Arquitetura do Sistema

A **Figura 01** apresenta a arquitetura geral do sistema **Água Inteligente**, composta pelos módulos *Edge*, *Ingestion*, *Analytics*, *Dashboard* e *Docs*.  
O fluxo de dados ocorre de forma sequencial: o módulo *Edge* coleta as informações de vazão de água (via sensores IoT ou simulador) e as envia ao módulo *Ingestion*, responsável por recebê-las através de uma API desenvolvida em **FastAPI**.  
Em seguida, o módulo *Analytics* realiza a análise dos dados, utilizando inicialmente regras estatísticas simples e, futuramente, algoritmos de **Machine Learning** para detecção automática de vazamentos.  
Os resultados são então disponibilizados ao módulo *Dashboard*, desenvolvido em **Streamlit**, que apresenta ao usuário final indicadores, gráficos e alertas de anomalia em tempo real.  
Por fim, o módulo *Docs* centraliza a documentação técnica e acadêmica do projeto, incluindo diagramas, relatórios e registros de versão.

![Figura 01 – Arquitetura do Sistema Água Inteligente](arquitetura_agua_inteligente.png)

**Figura 01 – Arquitetura do Sistema Água Inteligente.**  
Fonte: Elaborado pelos autores (2025).

---
