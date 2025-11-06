$pyArgs = @(
  '--noconfirm', '--onefile', '--console',
  '--name', 'AguaInteligente',

  # dados do projeto
  '--add-data', 'dashboard;dashboard',
  '--add-data', 'ingestion;ingestion',
  '--add-data', 'analytics;analytics',

  # coleta COMPLETA (código + dados) dos frameworks web
  '--collect-all', 'fastapi',
  '--collect-all', 'starlette',
  '--collect-all', 'pydantic',

  # todos os submódulos, para evitar imports dinâmicos faltantes
  '--collect-submodules', 'fastapi',
  '--collect-submodules', 'starlette',
  '--collect-submodules', 'pydantic',

  # reforços de imports implícitos
  '--hidden-import', 'fastapi',
  '--hidden-import', 'fastapi.applications',
  '--hidden-import', 'starlette.routing',
  '--hidden-import', 'starlette.responses',
  '--hidden-import', 'pydantic_core',
  '--hidden-import', 'typing_extensions',
  '--hidden-import', 'annotated_types',
  '--hidden-import', 'anyio',
  '--hidden-import', 'sniffio',
  '--hidden-import', 'h11',

  # data science
  '--collect-data', 'pandas',
  '--collect-data', 'numpy',

  'launcher.py'
)
