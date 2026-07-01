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
TAPER_CEILING = 125_140


@dataclass
class Band:
    name: str
    rate: float
    lower: float
    upper: float


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
    effective_rate: float
    marginal_rate: float
    bands: list = field(default_factory=list)


def calculate_personal_allowance(gross_income: float) -> float:
    """Apply the £1 lost for every £2 over £100,000 rule."""

    if gross_income <= TAPER_THRESHOLD:
        return PERSONAL_ALLOWANCE

    reduction = (gross_income - TAPER_THRESHOLD) / 2
    return max(0.0, PERSONAL_ALLOWANCE - reduction)


def get_ruk_bands(allowance: float) -> list[Band]:
    """
    rUK thresholds.

    HMRC thresholds are defined on gross income.
    Convert them into taxable-income thresholds using
    the person's actual allowance.
    """

    return [
        Band("Basic rate", 0.20, 0, 37_700),
        Band("Higher rate", 0.40, 37_700, 125_140 - allowance),
        Band("Additional rate", 0.45, 125_140 - allowance, float("inf")),
    ]


def get_scotland_bands(allowance: float) -> list[Band]:
    """
    Scottish thresholds.

    The Starter/Higher/Advanced limits are fixed taxable-income
    thresholds published by the Scottish Government.

    The Top Rate begins once gross income exceeds £125,140,
    so its taxable threshold depends on the remaining allowance.
    """

    return [
        Band("Starter rate", 0.19, 0, 3_967),
        Band("Basic rate", 0.20, 3_967, 16_956),
        Band("Intermediate rate", 0.21, 16_956, 31_092),
        Band("Higher rate", 0.42, 31_092, 62_430),
        Band("Advanced rate", 0.45, 62_430, 125_140 - allowance),
        Band("Top rate", 0.48, 125_140 - allowance, float("inf")),
    ]


REGIONS = {
    "ruk": {
        "label": "England, Wales & Northern Ireland",
        "bands": get_ruk_bands,
    },
    "scotland": {
        "label": "Scotland",
        "bands": get_scotland_bands,
    },
}


def calculate_tax(gross_income: float, region: str) -> TaxResult:

    if gross_income < 0:
        raise ValueError("gross_income cannot be negative")

    if region not in REGIONS:
        raise ValueError(f"Unknown region '{region}'")

    allowance = calculate_personal_allowance(gross_income)
    taxable_income = max(0.0, gross_income - allowance)

    bands = REGIONS[region]["bands"](allowance)

    results = []
    total_tax = 0.0
    marginal_rate = 0.0

    for band in bands:

        if taxable_income <= band.lower:
            continue

        upper = min(taxable_income, band.upper)

        amount = max(0.0, upper - band.lower)

        if amount == 0:
            continue

        tax = amount * band.rate

        total_tax += tax
        marginal_rate = band.rate

        results.append(
            BandResult(
                name=band.name,
                rate=band.rate,
                taxed_amount=round(amount, 2),
                tax_due=round(tax, 2),
            )
        )

    take_home = gross_income - total_tax

    return TaxResult(
        region=REGIONS[region]["label"],
        gross_income=round(gross_income, 2),
        personal_allowance=round(allowance, 2),
        taxable_income=round(taxable_income, 2),
        total_tax=round(total_tax, 2),
        take_home=round(take_home, 2),
        effective_rate=round(total_tax / gross_income, 4) if gross_income else 0.0,
        marginal_rate=marginal_rate,
        bands=results,
    )


def compare_regions(gross_income: float) -> dict:

    ruk = calculate_tax(gross_income, "ruk")
    scotland = calculate_tax(gross_income, "scotland")

    return {
        "ruk": ruk,
        "scotland": scotland,
        "difference": round(scotland.total_tax - ruk.total_tax, 2),
    }