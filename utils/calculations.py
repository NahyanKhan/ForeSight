"""
ForeSight — Calculation Utilities
Core math for runway, EMA, buyer reliability, Monte Carlo, and concentration risk.
"""

import numpy as np
import pandas as pd
from datetime import datetime


def exponential_moving_average(delays, span=5):
    """Calculate EMA of payment delays. Snaps quickly to recent behavior."""
    if not delays:
        return 0
    series = pd.Series(delays)
    return float(series.ewm(span=span, adjust=False).mean().iloc[-1])


def payment_velocity(delays):
    """
    Rate of change in payment delay.
    Positive = delays getting worse. Negative = improving.
    """
    if len(delays) < 2:
        return 0
    recent = delays[-3:] if len(delays) >= 3 else delays
    older = delays[:3] if len(delays) >= 3 else delays[:1]
    return float(np.mean(recent) - np.mean(older))


def empirical_90th_percentile(delays):
    """
    Use 90th percentile instead of μ + 1.5σ to respect lognormal distribution.
    """
    if not delays:
        return 0
    return float(np.percentile(delays, 90))


def compute_overdue_probability(buyer_invoices):
    """
    Compute the probability a buyer will be overdue based on historical data.
    Uses the fraction of past invoices that were overdue.
    """
    if not buyer_invoices:
        return 0.5  # default uncertainty
    overdue_count = sum(1 for inv in buyer_invoices if inv.get("is_overdue"))
    return overdue_count / len(buyer_invoices)


def risk_adjusted_receivables(open_invoices, overdue_probabilities):
    """
    Risk-Adjusted Receivables = Σ(invoice_amount × (1 − overdue_probability))
    """
    total = 0
    for inv in open_invoices:
        buyer_id = inv["buyer_id"]
        prob = overdue_probabilities.get(buyer_id, 0.5)
        total += inv["amount"] * (1 - prob)
    return total


def survival_runway(digital_reserves, cash_reserves, risk_adj_receivables, daily_burn):
    """
    Survival Runway = (Digital + Cash + Risk-Adjusted Receivables) / Daily Burn
    """
    if daily_burn <= 0:
        return 999
    return (digital_reserves + cash_reserves + risk_adj_receivables) / daily_burn


def monte_carlo_runway(digital_reserves, cash_reserves, open_invoices,
                       overdue_probabilities, daily_burn, simulations=5000):
    """
    Monte Carlo simulation for 80% confidence interval on runway.
    Samples overdue probability for each invoice to generate distribution.
    """
    runways = []
    for _ in range(simulations):
        adj_receivables = 0
        for inv in open_invoices:
            buyer_id = inv["buyer_id"]
            prob = overdue_probabilities.get(buyer_id, 0.5)
            # Simulate: does this invoice pay on time or not?
            pays = np.random.random() > prob
            if pays:
                adj_receivables += inv["amount"]
            else:
                # Partial recovery (30-70% for overdue invoices)
                recovery = np.random.uniform(0.3, 0.7)
                adj_receivables += inv["amount"] * recovery

        runway = (digital_reserves + cash_reserves + adj_receivables) / daily_burn if daily_burn > 0 else 999
        runways.append(runway)

    runways = np.array(runways)
    median = float(np.median(runways))
    ci_low = float(np.percentile(runways, 10))
    ci_high = float(np.percentile(runways, 90))

    return {
        "median": round(median),
        "ci_low": round(ci_low),
        "ci_high": round(ci_high),
        "distribution": runways,
    }


def concentration_risk(open_invoices):
    """
    Compute what % of total outstanding depends on each buyer.
    Returns sorted list of {buyer, amount, percentage}.
    """
    totals = {}
    for inv in open_invoices:
        buyer = inv.get("buyer_name", inv.get("buyer_id"))
        totals[buyer] = totals.get(buyer, 0) + inv["amount"]

    grand_total = sum(totals.values())
    if grand_total == 0:
        return []

    result = []
    for buyer, amount in sorted(totals.items(), key=lambda x: -x[1]):
        result.append({
            "buyer": buyer,
            "amount": amount,
            "percentage": round(amount / grand_total * 100, 1),
        })
    return result


def what_if_simulation(runway_data, buyer_id, additional_delay_days,
                       open_invoices, overdue_probabilities,
                       digital_reserves, cash_reserves, daily_burn):
    """
    Simulate "What if Buyer X delays by N more days?"
    Increases the overdue probability for that buyer and recalculates runway.
    """
    modified_probs = overdue_probabilities.copy()

    # Increase overdue probability based on delay
    current_prob = modified_probs.get(buyer_id, 0.5)
    delay_impact = min(additional_delay_days / 90.0, 0.4)  # max 40% increase
    modified_probs[buyer_id] = min(0.95, current_prob + delay_impact)

    return monte_carlo_runway(
        digital_reserves, cash_reserves, open_invoices,
        modified_probs, daily_burn
    )


def detect_retaliation(pre_volumes, post_volumes):
    """
    Deterministic two-sigma test for retaliation detection.
    Compares 30-day post-event mean against 90-day pre-event distribution.
    Returns dict with is_retaliation, p_value, drop_percentage.
    """
    if len(pre_volumes) < 10 or len(post_volumes) < 5:
        return {"is_retaliation": False, "reason": "insufficient_data"}

    pre_mean = np.mean(pre_volumes)
    pre_std = np.std(pre_volumes)
    post_mean = np.mean(post_volumes)

    if pre_std == 0:
        return {"is_retaliation": False, "reason": "zero_variance"}

    z_score = (pre_mean - post_mean) / pre_std
    drop_pct = ((pre_mean - post_mean) / pre_mean) * 100 if pre_mean > 0 else 0

    # Two-sigma threshold
    from scipy import stats
    p_value = 1 - stats.norm.cdf(z_score)

    return {
        "is_retaliation": z_score > 2.0,
        "z_score": round(z_score, 2),
        "p_value": round(p_value, 4),
        "drop_percentage": round(drop_pct, 1),
        "pre_mean": round(pre_mean, 1),
        "post_mean": round(post_mean, 1),
    }
