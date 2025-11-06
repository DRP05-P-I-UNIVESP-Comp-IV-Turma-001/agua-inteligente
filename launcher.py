# launcher.py — estável (sem loops), com sys.path hack e abertura automática do navegador
import os
import sys
import time
import threading
import requests

# --- Torna ingestion/analytics/dashboard importáveis no .exe (PyInstaller) e no dev ---
BASE = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
for sub in ("ingestion", "analytics", "dashboard"):
    p = os.path.join(BASE, sub)
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)
# --------------------------------------------------------------------------------------

# Config central (boas práticas: deixar no dashboard/config.py)
from dashboard.config import API_HOST, API_PORT, DASHBOARD_PORT, API_BASE


def is_port_busy(port: int, host: str = "127.0.0.1") -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.25)
        return s.connect_ex((host, port)) == 0


def wait_health(tries: int = 30, delay: float = 1.0) -> bool:
    """Espera o /health do backend responder 200 OK."""
    url = f"{API_BASE}/health"
    for _ in range(tries):
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                print("[OK] Backend ativo.")
                return True
        except Exception:
            pass
        time.sleep(delay)
    print("[ERRO] Backend não respondeu dentro do tempo limite.")
    return False


def run_backend():
    import uvicorn
    from ingestion.main import app  # ✅ importa o módulo explicitamente
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info",
        reload=False,
    )



def run_dashboard(open_browser: bool = True) -> int:
    """
    Inicia o Streamlit pela CLI oficial (evita bug do bootstrap.run).
    Se open_browser=True, o navegador abre automaticamente.
    """
    import streamlit.web.cli as stcli

    script_path = os.path.join(BASE, "dashboard", "app.py")
    if not os.path.exists(script_path):
        print(f"[ERRO] {script_path} não encontrado")
        return 1

    # Config estável: sem dev server (:3000) e sem variáveis de porta conflitantes
    os.environ["STREAMLIT_DEV_SERVER"] = "0"
    os.environ.pop("BROWSER_SERVER_PORT", None)
    os.environ.pop("STREAMLIT_BROWSER_SERVER_PORT", None)

    # Portas e headless
    args = [script_path, "--server.port", str(DASHBOARD_PORT)]
    if open_browser:
        # headless false permite abrir o navegador automaticamente
        os.environ["STREAMLIT_SERVER_HEADLESS"] = "false"
    else:
        args += ["--server.headless", "true"]

    # Opcional: desativa telemetria do Streamlit
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    # Executa o app
    stcli.main_run(args)
    return 0


def main() -> int:
    # Sobe o backend se a porta não estiver ocupada
    if not is_port_busy(API_PORT, API_HOST):
        threading.Thread(target=run_backend, daemon=True).start()

    # Espera o backend ficar OK
    if not wait_health():
        return 1

    # Inicia o dashboard (abre navegador automaticamente)
    return run_dashboard(open_browser=True)


if __name__ == "__main__":
    # Evita loop de reloader no PyInstaller/Streamlit
    if os.environ.get("IS_RELOADER", "0") == "1":
        sys.exit(0)
    sys.exit(main())
