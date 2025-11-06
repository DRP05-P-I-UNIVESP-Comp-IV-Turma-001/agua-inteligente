# dashboard/config.py
import os, sys
from zoneinfo import ZoneInfo

# Detecta se está empacotado pelo PyInstaller
IS_FROZEN = bool(getattr(sys, "frozen", False))

# Portas padrão (DEV x .EXE)
DEV_API_PORT, DEV_DASH_PORT = 8000, 8501
EXE_API_PORT, EXE_DASH_PORT = 8010, 8510

# Host/port dinâmicos (podem ser alterados por variáveis de ambiente)
API_HOST = os.getenv("AI_API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("AI_API_PORT", EXE_API_PORT if IS_FROZEN else DEV_API_PORT))
DASHBOARD_PORT = int(os.getenv("AI_DASHBOARD_PORT", EXE_DASH_PORT if IS_FROZEN else DEV_DASH_PORT))

# Compatibilidade com variável antiga (se definida, sobrescreve)
API_BASE = os.getenv("AGUA_API_BASE", f"http://{API_HOST}:{API_PORT}")

# Fuso horário
TIMEZONE = ZoneInfo(os.getenv("AGUA_TZ", "America/Sao_Paulo"))
