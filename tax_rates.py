"""
UK Income Tax calculation logic for tax year 2026/27.

Two separate regimes are modelled:
- rUK: England, Wales, Northern Ireland (3 bands, set by UK Government/HMRC)
- Scotland: set independently by the Scottish Parliament (6 bands)

Both regimes share the same UK-wide Personal Allowance and the same
taper rule (lose £1 of allowance for every £2 earned over £100,000,
fully gone by £125,140).

Sources (verified June 2026):
- gov.scot Scottish Income Tax 2026/27 technical factsheet
- mygov.scot current Income Tax rates
- gov.uk / HMRC Income Tax rates and Personal Allowances (rUK, frozen since 2021)

This module has no Flask dependency so it can be unit tested and reused
(e.g. from a CLI or another framework) independently of the web layer.
"""

from dataclasses import dataclass, field

PERSONAL_ALLOWANCE = 12_570
TAPER_THRESHOLD = 100_000
TAPER_CEILING = 125_140  # allowance reaches £0 here


@dataclass
class Band:
    name: str
    rate: float          # e.g. 0.20 for 20%
    lower: int            # lower bound of taxable income (after allowance), inclusive
    upper: float           # upper bound, exclusive; float('inf') for top band


@dataclass
class BandResult:
    name: str
    rate: float
    taxed_amount: float
    tax_due: float


@dataclass
class TaxResult:
    region: str
    gross_income: float
    personal_allowance: float
    taxable_income: float
    total_tax: float
    take_home: float
    effective_rate: float          # total_tax / gross_income
    marginal_rate: float           # rate applying to the next £1 earned
    bands: list = field(default_factory=list)  # list[BandResult]


# rUK: England, Wales, Northern Ireland — 3 bands
RUK_BANDS = [
    Band("Basic rate", 0.20, 0, 37_700),
    Band("Higher rate", 0.40, 37_700, 125_140 - PERSONAL_ALLOWANCE),
    Band("Additional rate", 0.45, 125_140 - PERSONAL_ALLOWANCE, float("inf")),
]

# Scotland — 6 bands (thresholds below are on TAXABLE income, i.e. after
# the £12,570 personal allowance has already been deducted)
SCOTLAND_BANDS = [
    Band("Starter rate", 0.19, 0, 3_967),
    Band("Basic rate", 0.20, 3_967, 16_956),
    Band("Intermediate rate", 0.21, 16_956, 31_092),
    Band("Higher rate", 0.42, 31_092, 62_430),
    Band("Advanced rate", 0.45, 62_430, 125_140 - PERSONAL_ALLOWANCE),
    Band("Top rate", 0.48, 125_140 - PERSONAL_ALLOWANCE, float("inf")),
]

REGIONS = {
    "ruk": {"label": "England, Wales & Northern Ireland", "bands": RUK_BANDS},
    "scotland": {"label": "Scotland", "bands": SCOTLAND_BANDS},
}


def calculate_personal_allowance(gross_income: float) -> float:
    """Apply the £1-lost-per-£2-over-£100k taper. Allowance hits £0 at £125,140."""
    if gross_income <= TAPER_THRESHOLD:
        return PERSONAL_ALLOWANCE
    reduction = (gross_income - TAPER_THRESHOLD) / 2
    return max(0.0, PERSONAL_ALLOWANCE - reduction)


def calculate_tax(gross_income: float, region: str) -> TaxResult:
    """Calculate income tax for a given gross salary and region ('ruk' or 'scotland')."""
    if region not in REGIONS:
        raise ValueError(f"Unknown region '{region}'. Must be one of {list(REGIONS)}")
    if gross_income < 0:
        raise ValueError("gross_income cannot be negative")

    allowance = calculate_personal_allowance(gross_income)
    taxable_income = max(0.0, gross_income - allowance)

    bands = REGIONS[region]["bands"]
    band_results = []
    total_tax = 0.0
    marginal_rate = 0.0

    for band in bands:
        if taxable_income <= band.lower:
            continue
        upper = band.upper if band.upper != float("inf") else taxable_income
        amount_in_band = min(taxable_income, upper) - band.lower
        amount_in_band = max(0.0, amount_in_band)
        if amount_in_band <= 0:
            continue
        tax_in_band = amount_in_band * band.rate
        total_tax += tax_in_band
        marginal_rate = band.rate
        band_results.append(
            BandResult(
                name=band.name,
                rate=band.rate,
                taxed_amount=round(amount_in_band, 2),
                tax_due=round(tax_in_band, 2),
            )
        )

    take_home = gross_income - total_tax
    effective_rate = (total_tax / gross_income) if gross_income > 0 else 0.0

    return TaxResult(
        region=REGIONS[region]["label"],
        gross_income=gross_income,
        personal_allowance=round(allowance, 2),
        taxable_income=round(taxable_income, 2),
        total_tax=round(total_tax, 2),
        take_home=round(take_home, 2),
        effective_rate=round(effective_rate, 4),
        marginal_rate=marginal_rate,
        bands=band_results,
    )


def compare_regions(gross_income: float) -> dict:
    """Convenience helper: calculate both regions and the difference between them."""
    ruk = calculate_tax(gross_income, "ruk")
    scotland = calculate_tax(gross_income, "scotland")
    return {
        "ruk": ruk,
        "scotland": scotland,
        "difference": round(scotland.total_tax - ruk.total_tax, 2),  # +ve = Scotland pays more
    }
