# TradingAgents Web Console

The TradingAgents Web Console is an interactive, real-time web dashboard for orchestrating multi-agent backtesting sweeps, streaming agent debate logs live, and analyzing investment decisions scored against market benchmark Alpha.

---

## 🚀 Quick Start

### 1. Install Web Dependencies

The web console requires FastAPI, Uvicorn, and SSE support:

```bash
pip install ".[web]"
# or in editable development mode:
pip install -e ".[web]"
```

### 2. Launch the Web Interface

Start the web server and automatically open your default browser:

```bash
tradingagents web
```

Alternatively, run directly from source:

```bash
python -m cli.main web
```

The console opens at [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## ⚙️ CLI Options

The `tradingagents web` command supports several command-line flags:

```bash
tradingagents web [OPTIONS]
```

| Flag | Default | Description |
| :--- | :--- | :--- |
| `--port INTEGER` | `8000` | Port to bind the server to (e.g. `--port 8080`) |
| `--host TEXT` | `127.0.0.1` | Network host address (`0.0.0.0` allows LAN or remote server access) |
| `--open / --no-open` | `--open` | Open default browser automatically (`--no-open` for headless / VPS) |
| `--dev` | `False` | Enable auto-reloading for backend API code changes |

### Examples

- **Headless server / Docker / Remote VPS:**
  ```bash
  tradingagents web --host 0.0.0.0 --port 8000 --no-open
  ```

- **Run on a custom port:**
  ```bash
  tradingagents web --port 3000
  ```

- **Backend development mode:**
  ```bash
  tradingagents web --dev --no-open
  ```

---

## 🔑 Environment Configuration

Set your model API keys in your `.env` file or export them in your terminal before launching:

```bash
# Providers
export NVIDIA_API_KEY="nvapi-..."         # NVIDIA NIM
export OPENAI_API_KEY="sk-..."            # OpenAI (GPT-5, GPT-6)
export ANTHROPIC_API_KEY="sk-ant-..."     # Anthropic (Claude)
export GOOGLE_API_KEY="..."               # Google (Gemini)
export GROQ_API_KEY="gsk_..."             # Groq
export OPENROUTER_API_KEY="sk-or-..."     # OpenRouter
export DEEPSEEK_API_KEY="sk-..."          # DeepSeek
export OLLAMA_BASE_URL="http://localhost:11434/v1"  # Ollama

# Optional Market & Screening Data
export FRED_API_KEY="..."                 # Macro data
export ALPHA_VANTAGE_API_KEY="..."        # Historical financials
```

---

## 🖥️ Web Console Features

### 1. Configuration Panel
- **Ticker Selection & Presets:** Choose from built-in presets (*Tech Giants*, *Semiconductors*, *Gold & Commodities*, *Crypto Top*) or enter custom tickers (`NVDA, AAPL`, `BTC, ETH`, `GOLD, XAUUSD`).
- **Dynamic Model Fetching:** Automatically queries live models for selected providers (NVIDIA NIM, Groq, OpenRouter, Ollama, OpenAI, Anthropic, Gemini) with fallback catalogs and custom model IDs.
- **Analyst Squad Selection:** Select which agent analysts to deploy (*Market Analyst*, *Social Sentiment Analyst*, *News Analyst*, *Fundamentals Analyst*).
- **Sweep Parameters:** Configure date ranges, sweep intervals (every $N$ days), and asset types (`stock` or `crypto`).

### 2. Live Execution Monitor
- **Real-Time Progress:** View overall progress percentage, active cell ticker, and execution date.
- **Live Streaming Terminal:** Server-Sent Events (SSE) stream terminal logs, agent debate reasoning, and risk management assessments with auto-scroll.
- **Execution Controls:** 
  - **Stop Sweep:** Immediately halts execution without hanging the engine.
  - **Reset Engine:** Clear state back to `idle` in case of timeouts or network disruptions.

### 3. Results & Analytics
- **Benchmark Alpha Performance:** Directional Hit Rate (%) and Mean Alpha (%) evaluated against benchmark index closes.
- **Rating Breakdown:** Visual bar chart of decisions (*Strong Buy*, *Buy*, *Hold*, *Sell*, *Strong Sell*).
- **Interactive Cell Table:** Filter and inspect every analysis cell, view comprehensive researcher debates, and audit final trade recommendations.

### 4. Historical Backtests
- Browse and inspect past backtest logs stored in `~/.tradingagents/logs/backtest/`.
- Status indicators clearly display **Running**, **Stopped**, or **Viewing** without stale active states.

### 5. Data & MCP Server Management
- **Vietnam Market Data Infrastructure:** Live connection status and tool metrics for **AlgoLab MCP** (primary price and index data) and **SSI Securities MCP** (fallback and news co-sourcing).
- **1-Click SSI OAuth 2.0 PKCE:** Connect SSI account via browser popup; tokens automatically rotate unattended with single-use refresh tokens (RFC 6749).
- **AlgoLab Key & Quota Management:** Save `ALGOLAB_API_KEY` to `.env` directly from the Web UI and inspect live daily request quota.
- **Connection Diagnostics:** Integrated test connection probes reporting latency (ms) and registered tool counts.

---

## 🛠️ Frontend Development & Building

The frontend is built with **React 19**, **Vite**, **TypeScript**, **Tailwind CSS**, and **shadcn/ui**.

### Project Structure
```
web/
├── dist/                # Pre-built production bundle served by FastAPI
├── src/
│   ├── components/      # React UI components (ConfigPanel, LiveMonitor, ResultsPanel, HistoryPanel, Header)
│   ├── components/ui/   # Primitive UI widgets (button, card, badge, tabs, input, progress)
│   ├── lib/             # API client functions (fetchConfig, startBacktest, stopBacktest, resetBacktest)
│   ├── types.ts         # TypeScript interfaces for API requests and schemas
│   ├── App.tsx          # Main application orchestrator
│   └── main.tsx         # React root entry point
├── package.json
├── tailwind.config.js
└── vite.config.ts
```

### Running Frontend in Dev Mode (Hot-Reload)

1. Start the FastAPI backend:
   ```bash
   tradingagents web --no-open --dev
   ```

2. In a separate terminal, start Vite dev server:
   ```bash
   cd web
   npm install
   npm run dev
   ```
   Open [http://localhost:5173](http://localhost:5173). Requests to `/api/*` are automatically proxied to FastAPI on port 8000.

### Building for Production

When making frontend edits, rebuild the static assets for FastAPI to serve:

```bash
cd web
npm run build
```
This bundles everything into `web/dist/`, which is directly mounted at `/` by FastAPI in `tradingagents/api/app.py`.

---

## 📡 Backend API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status |
| `GET` | `/api/config` | Retrieve default settings, providers, and analysts |
| `GET` | `/api/config/models?provider={name}` | Live fetch supported LLM models for a provider |
| `POST` | `/api/backtest/run` | Launch a new backtest sweep |
| `POST` | `/api/backtest/stop` | Terminate the active backtest run |
| `POST` | `/api/backtest/reset` | Force reset engine state to idle |
| `GET` | `/api/backtest/status` | Current runner status and active run ID |
| `GET` | `/api/backtest/events` | Server-Sent Events (SSE) real-time stream |
| `GET` | `/api/backtest/runs` | List historical backtest runs |
| `GET` | `/api/backtest/runs/{run_id}` | Detailed cell entries and score summary for a run |
