import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from tax_rates import calculate_tax, calculate_personal_allowance, compare_regions


class TestPersonalAllowance:
    def test_below_taper_threshold(self):
        assert calculate_personal_allowance(50_000) == 12_570

    def test_at_taper_threshold(self):
        assert calculate_personal_allowance(100_000) == 12_570

    def test_within_taper(self):
        # £110,000: lose £1 per £2 over £100k -> lose £5,000
        assert calculate_personal_allowance(110_000) == 7_570

    def test_fully_tapered(self):
        assert calculate_personal_allowance(125_140) == 0

    def test_above_full_taper(self):
        assert calculate_personal_allowance(200_000) == 0


class TestRUK:
    def test_below_personal_allowance_pays_nothing(self):
        result = calculate_tax(10_000, "ruk")
        assert result.total_tax == 0

    def test_basic_rate_only(self):
        # £30,000: taxable = 30,000 - 12,570 = 17,430, all at 20%
        result = calculate_tax(30_000, "ruk")
        assert result.total_tax == pytest.approx(17_430 * 0.20, abs=0.01)

    def test_crosses_into_higher_rate(self):
        # £60,000 gross: basic band tax (37,700*0.20) + remainder at 40%
        result = calculate_tax(60_000, "ruk")
        taxable = 60_000 - 12_570
        expected = 37_700 * 0.20 + (taxable - 37_700) * 0.40
        assert result.total_tax == pytest.approx(expected, abs=0.01)

    def test_additional_rate_at_150k(self):
        result = calculate_tax(150_000, "ruk")
        assert result.marginal_rate == 0.45
        assert result.personal_allowance == 0  # fully tapered


class TestScotland:
    def test_starter_rate_band(self):
        # £15,000 gross -> £2,430 taxable, all in 19% starter band
        result = calculate_tax(15_000, "scotland")
        assert result.total_tax == pytest.approx(2_430 * 0.19, abs=0.01)

    def test_reference_29526_gross(self):
        # Published reference: £29,526 gross => £3,351 total tax
        # (19% on 3,967 + 20% on 12,989)
        result = calculate_tax(29_526, "scotland")
        assert result.total_tax == pytest.approx(3_351, abs=1)

    def test_reference_100k_gross(self):
        # Published reference: £100,000 gross => £30,732 in Scotland
        result = calculate_tax(100_000, "scotland")
        assert result.total_tax == pytest.approx(30_732, abs=5)

    def test_top_rate_above_125140(self):
        result = calculate_tax(200_000, "scotland")
        assert result.marginal_rate == 0.48


class TestComparison:
    def test_scotland_generally_higher_above_crossover(self):
        # At £100k, published gap is ~£3,300 in favour of rUK taxpayer
        comp = compare_regions(100_000)
        assert comp["difference"] == pytest.approx(3_300, abs=10)

    def test_low_earners_pay_slightly_less_in_scotland(self):
        # Below ~£30,300, Scotland is meant to be marginally cheaper
        comp = compare_regions(20_000)
        assert comp["difference"] < 0

    def test_invalid_region_raises(self):
        with pytest.raises(ValueError):
            calculate_tax(50_000, "wales_only")

    def test_negative_income_raises(self):
        with pytest.raises(ValueError):
            calculate_tax(-100, "ruk")
