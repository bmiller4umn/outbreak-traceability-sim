# FSMA 204 Outbreak Traceability Simulation

Interactive simulation comparing deterministic (full FSMA 204 compliance) vs probabilistic lot code tracing in food supply chain outbreak investigations.

## Features

- **Supply Chain Simulation**: Configurable network of farms, packers, distribution centers, and retailers
- **Contamination Modeling**: Simulate pathogen spread through the supply chain
- **Dual Tracing Modes**: Compare deterministic (1:1 lot links) vs probabilistic (calculated) traceability
- **Monte Carlo Analysis**: Run thousands of iterations for statistical comparison
- **Investigation Timing**: Estimate real-world investigation duration
- **Interactive Visualization**: D3.js network graphs and investigation flow

## Quick Start

### Local Development

```bash
# Backend
pip install -e ".[web]"
uvicorn outbreak_traceability_sim.api.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

Or manually:
1. Push to GitHub
2. Connect repo to Render
3. Render auto-detects `render.yaml`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_MONTE_CARLO_ITERATIONS` | 10000 | Max iterations allowed |
| `DEFAULT_MONTE_CARLO_ITERATIONS` | 1000 | Default iteration count |
| `CORS_ORIGINS` | localhost | Allowed CORS origins |

## License

MIT
