# AlgoLab MCP Findings

Date: 2026-11-03. Evidence: public docs at `mcp.algolab.vn/docs/*.md`, public OAuth metadata, and 15 paced anonymous calls to `https://mcp.algolab.vn/free`. No account or API key was used.

## Verdict

GO for unattended backend use, subject to quota and the provider's terms. Paid-plan behavior was not tested.

## Access

- Operator: CTCP Tập đoàn Algospace. Server `algolab-market-data` v2.1.0, protocol 2025-03-26.
- Endpoints: `https://mcp.algolab.vn` (OAuth or API key), `https://mcp.algolab.vn/free` (anonymous).
- API key: `Authorization: Bearer alm_...`, no browser flow. This is the simplest unattended path.
- OAuth: dynamic registration, PKCE S256, refresh tokens. Access token 30 days, reconnect after 90 idle days (docs).
- Tools: 12 direct tools plus specialized functions through `call_function`. Response shape `{status, data, meta}`, with `meta.quota`.

## Quota

| Plan | Price per month | Calls per day | Notes |
|---|---|---|---|
| Free / Lite | 0 | 1,000 shared system-wide | 120 per minute; 200 per person in 5 hours |
| Plus | 129,000 VND | 1,000 private | No 5-hour limit |
| Pro | 199,000 VND | 2,000 private | No 5-hour limit |
| Max | 999,000 VND | 10,000 private | No 5-hour limit |

## Observed

| Check | Result |
|---|---|
| `get_price_history` VNM, 2014-01-02 to 2014-01-10 | Bars returned, `from_date`/`to_date` work |
| `get_price_history` VNINDEX, same window | Index bars returned |
| SHS (HNX, absent on Yahoo test) and VEA | Bars returned |
| BVH statements | `form: INSURANCE`, insurance line items |
| VCB statements, `limit=20` | `form: BANK`, oldest period 2021-Q4 |
| `get_macro(vietnam)` | CPI and GDP series returned |
| FPT news, `from_date=2020-01-01`, `limit=100` | 56 items only, oldest 2026-10-06 |

## Limits That Affect Design

- News depth: the FPT sample reaches back about 4 weeks. It cannot serve historical news.
- Statements have no date parameter and no publication date; `limit` caps at 20 periods. Filter by period and apply a reporting lag.
- Daily bars are back-adjusted using dividends dated after the bar. `c_actual` is an estimate rounded to 10 VND. Use one adjustment convention for a run and do not splice vendors within a price series.
- Foreign flow in bars is null in 2014; docs state market-wide flow from 01/2024. Per-ticker start date was not determined.
- During or before a session, the latest bar can have `v=0` and copied prices. Observed on 2026-11-03. Drop it.
- Macro `date` is the period end, not the release date. Apply a lag; revisions are not point-in-time.
- Profile, valuation and most signals are current-only. `get_market_overview` accepts `as_of`.
- Docs disagree on index history: tool text says 2013, changelog says 08/2017. The 2014 VNINDEX sample supports 2013 or earlier coverage.

## Terms

- Data is for reference and personal analysis. Raw data may not be redistributed, resold, or have access shared.
- Broker reports are copyrighted by their publishers.
- Call logs, with parameters up to 1 KB, are kept 60 days. `search` queries go to Google Gemini.
- Full terms at `algolab.vn/terms#mcp` were not read. Automated use and local retention still need confirmation.
- Personal use fits. A multi-user hosted Web UI would need provider approval.
