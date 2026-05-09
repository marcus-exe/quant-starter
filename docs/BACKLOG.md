# Quant-Starter — Backlog de testes / extensões

Roadmap solto. Marca `[x]` quando implementar.

## Validação estatística

- [ ] Walk-forward / rolling window (reotimiza in-sample, valida out-of-sample)
- [ ] Monte Carlo bootstrap dos trades (distribuição de Sharpe / MaxDD)
- [ ] Permutation test sinal vs returns embaralhados
- [ ] Deflated Sharpe Ratio (López de Prado) — correção multiple testing
- [ ] Reality Check / SPA test p/ comparação entre estratégias

## Estratégias novas

- [x] Mean reversion RSI(2) em SPY
- [x] Bollinger band fade em ETFs
- [x] Pairs trading / cointegration: KO/PEP (rolling OLS hedge + z-score)
- [x] Vol targeting wrapper (escala posição p/ realized vol alvo, ex: 10%)
- [x] Risk parity no universo xsmom (pesos inversos a vol)
- [x] Carry / term structure: VIX (SVXY long quando VIX/VIX3M < 1) — treasury curve pendente
- [ ] Cross-sectional value/quality via Polygon fundamentals
- [x] Trend-following multi-timeframe (Donchian breakout 20/10)
- [x] Seasonality turn-of-month — FOMC drift pendente

## Microestrutura / execução

- [ ] Slippage modelado (VWAP, spread, market impact)
- [ ] Limit vs market order sim com fill probability
- [ ] Bid/ask 1m bars (yfinance/Polygon) p/ intraday
- [ ] Latency sensitivity (atraso 1/5/15min, plota degradação)
- [ ] Partial fills

## Risco

- [ ] VaR + CVaR histórico e paramétrico vs realized
- [ ] Drawdown control (vol target + stop-loss agregado)
- [ ] Kelly sizing fracionário vs equal-weight
- [ ] Correlation regime detection (HMM ou breakpoint)
- [ ] Stress test replay: 2008, 2020-03, 2022
- [ ] Tail-risk hedge overlay (puts OTM, VIX calls)

## Dados / infra

- [ ] Survivorship bias check (delisted tickers se expandir universe)
- [ ] Corporate actions: validar split/dividend adjustment yfinance
- [ ] Backfill Polygon minute bars no Timescale
- [ ] Parquet snapshot p/ MinIO + restore path
- [ ] Reprodutibilidade: hash config + seed, rerun bate metrics
- [ ] Data quality checks (gaps, outliers, stale prices)
- [ ] Timezone / DST sanity tests

## ML layer

- [ ] Feature store (momentum, vol, RSI como colunas no Timescale)
- [ ] Meta-labeling (López de Prado): classifier decide seguir sinal base
- [ ] Triple barrier labeling + XGBoost/LightGBM
- [ ] Regime classifier (bull/bear/chop) ativa estratégia condicional
- [ ] Feature importance + purged k-fold CV
- [ ] LSTM / transformer baseline (não pra produção, só benchmark)

## Operacional

- [ ] Reconciliação Alpaca positions vs DB esperado + alerta drift
- [ ] Kill switch (daily loss limit halt orders)
- [ ] Paper → live shadow (roda live só log, compara fills)
- [ ] Backtest vs paper divergence report (slippage real vs assumido)
- [ ] Monitoring dashboard (Grafana sobre Timescale)
- [ ] Alertas Telegram/Slack em fills + drawdown

## Prioridade sugerida

1. Walk-forward
2. Vol targeting
3. Deflated Sharpe
4. Reconciliação Alpaca
5. Mean reversion strategy
