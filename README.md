## Author

**Muhammad Sarim Janjua**
GitHub:https://github.com/msarimgit

# UK Income Tax Calculator — rUK vs Scotland

A small Flask app that compares take-home pay under the two different UK
income tax regimes for the 2026/27 tax year:

- **England, Wales & Northern Ireland** — 3 bands, set by HMRC
- **Scotland** — 6 bands, set independently by the Scottish Parliament

Enter a gross salary and see a live, side-by-side breakdown of exactly which
band each pound falls into, and how much more (or less) tax you'd pay north
or south of the border.

**Live demo:** _add your Railway URL here once deployed_

## Why this exists

Scotland's income tax bands genuinely diverge from the rest of the UK —
different thresholds, an extra 3 bands, and a different marginal rate at
almost every income level above ~£16.5k. Most take-home pay calculators
either ignore this or bury it. This one puts both systems side by side.

## Stack

- **Backend:** Flask (Python), pure-function tax logic decoupled from the web layer
- **Frontend:** vanilla HTML/CSS/JS — no build step
- **Tests:** pytest, validated against published HMRC/gov.scot reference figures
- **Deploy:** Railway (Procfile + `railway.json`, gunicorn)

## Project structure

```
uk-tax-calculator/
├── app.py                  # Flask routes (HTML page + JSON API)
├── tax_rates.py            # Framework-agnostic tax calculation logic
├── tests/
│   └── test_tax_rates.py   # pytest suite
├── templates/
│   └── index.html
├── static/
│   ├── css/style.css
│   └── js/main.js
├── requirements.txt
├── requirements-dev.txt
├── Procfile
└── railway.json
```

## Running locally

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

python3 app.py                    # http://localhost:5000
```

## Running tests

```bash
pytest tests/ -v
```

The test suite checks band boundaries, the Personal Allowance taper
(£1 lost per £2 earned over £100,000, gone entirely at £125,140), and
cross-checks totals against published reference figures — e.g. £29,526
gross in Scotland should produce £3,351 of tax; £100,000 gross should show
a ~£3,300 gap in favour of the rUK taxpayer.

## API

`GET /api/calculate?income=45000`

Returns a JSON breakdown for both regions plus the difference between them:

```json
{
  "ruk": { "total_tax": 6486.0, "take_home": 38514.0, "bands": [...] },
  "scotland": { "total_tax": 6882.05, "take_home": 38117.95, "bands": [...] },
  "difference": 396.05
}
```

## Deploying to Railway

1. Push this repo to GitHub.
2. In Railway, create a new project → **Deploy from GitHub repo**.
3. Railway auto-detects Python via Nixpacks and reads the `Procfile` /
   `railway.json` for the start command — no manual config needed.
4. Once deployed, Railway gives you a public URL. Update the "Live demo"
   link above.

No environment variables are required for this app to run.

## Limitations

This is illustrative only — it does not account for National Insurance,
student loan repayments, pension contributions, dividend income, or
Scottish-specific reliefs. It isn't tax advice. Rates are for the 2026/27
tax year and are hardcoded in `tax_rates.py`; they'll need updating at each
UK and Scottish Budget.

## License

MIT — see [LICENSE](LICENSE).l
