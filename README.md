# MIP Retail Optimizer Enterprise

Aplicación de optimización de redes de centros de distribución. La interfaz React/Vite se compila como sitio estático y se empaqueta en una ventana de escritorio PyWebView; las decisiones de apertura y asignación se resuelven en Python con PuLP y el solver CBC.

## Arquitectura

- `frontend_web/src/`: interfaz React, dashboard, escenarios, gráficos y asistente.
- `frontend_web/dist/`: resultado estático de `npm run build`, cargado localmente por PyWebView.
- `desktop_app.py`: puente JavaScript/Python. Expone la resolución de escenarios y el asistente Gemini a la interfaz.
- `optimizacion.py`: modelo MIP PuLP/CBC reutilizable y ejecución de línea de comandos.
- `GEMINI_API_KEY`: configuración local opcional para el asistente. La optimización funciona sin esta clave ni conexión a internet.

El puente entrega al frontend el mismo contrato JSON `OptimizationResult` usado por los componentes React. En Windows, CBC se inicia sin ventana de consola.

## Desarrollo

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Set-Location frontend_web
npm install
npm run build
Set-Location ..
python desktop_app.py
```

Para el asistente, crea `.env` en la raíz con `GEMINI_API_KEY=tu_clave`. También puede definirse esa variable en el entorno. No publiques la clave.

## Compilar para Windows

Con `.venv` activado, instala las dependencias y PyInstaller. Compila primero el frontend. Después ejecuta:

```powershell
pyinstaller --noconfirm --onefile --windowed --name "MIP_Retail_Optimizer" --add-data "frontend_web/dist;frontend_web/dist" --collect-all pulp --collect-all webview --collect-all google.genai desktop_app.py
```

El ejecutable queda en `dist/MIP_Retail_Optimizer.exe`. Si existe un `.env` local, inclúyelo en el bundle con `--add-data ".env;."`; ese archivo contiene secretos y debe permanecer fuera de Git. El asistente requiere internet y una clave Gemini válida; el motor PuLP/CBC opera localmente.

## Caso de estudio

El modelo asigna la demanda de seis zonas a cuatro ubicaciones candidatas. Minimiza costos fijos y de transporte, cubre toda la demanda, respeta capacidades y limita el número de centros abiertos. Los parámetros oficiales y la matriz de tarifas están en `optimizacion.py` y `frontend_web/src/data/defaults.ts`.

Para ejecutar el motor desde la terminal:

```powershell
python optimizacion.py
```

## Git y artefactos locales

`.env`, `frontend_web/node_modules/`, `frontend_web/dist/`, `build/` y `dist/` están excluidos de Git. El repositorio contiene el código fuente; el ejecutable se genera localmente con PyInstaller.
