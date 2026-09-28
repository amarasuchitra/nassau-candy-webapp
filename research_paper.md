# Factory Reallocation & Shipping Optimization for Nassau Candy Distributor
### Research Paper — MVP Analysis

---

## 1. Problem Statement

Nassau Candy currently assigns products to factories using static, legacy rules
(5 factories, each locked to a fixed product list). This causes suboptimal
shipping distances, elevated lead times in some regions, and margin erosion
from logistics — with no system in place to simulate reassignment scenarios
before acting on them. This project builds that system: a predictive model of
shipping lead time, a what-if simulation engine, and a ranked recommendation
dashboard.

## 2. Data

The source file contains 10,194 orders (Jan 2024 – Dec 2025) across 15
products in 3 divisions (Chocolate, Sugar, Other), shipped to customers across
59 US states/Canadian provinces, grouped into 4 regions (Interior, Atlantic,
Gulf, Pacific). No fields were missing.

**Volume is heavily concentrated:** the five Wonka Bar chocolate SKUs account
for 9,844 of 10,194 orders (96.6%). The ten Sugar/Other SKUs together account
for the remaining 350 orders, and several individual products (Nerds,
Hair Toffee, Everlasting Gobstopper, Fun Dip) have fewer than five orders each.
Any conclusion about those products is necessarily low-confidence and is
flagged as such throughout the dashboard.

## 3. Critical Data Quality Finding

The brief asks for lead time computed as `Ship Date − Order Date`. We
computed this and found it unusable:

- Raw lead time averages **1,321 days** (min 904, max 1,642) — i.e. 2.5 to
  4.5 *years*, not days. Every Ship Date sits a whole number of years (2, 3,
  or 4) ahead of its Order Date.
- After removing that whole-year offset, the residual varies by **under one
  day** across factories (std. dev. 0.26 days) and shows **no correlation**
  with shipping distance (r = −0.03).

**Conclusion:** the Ship Date field in this export does not encode real
shipping performance — it is a data-generation or ETL artifact. Building a
lead-time model directly on it would mean fitting noise and would produce
reassignment recommendations disconnected from actual logistics.

**How we handled it:** rather than block the project on a data-pipeline fix,
we built the required model on a transparent, formula-grounded **lead-time
estimate**:

```
estimated_lead_time = ship_mode_base_days
                     + shipping_distance_miles / 500      (avg. transit speed)
                     + division_handling_allowance
                     + small random variation (σ = 0.3 days)
```

This uses only levers that genuinely matter to the business question
(distance and ship mode), is fully documented, and is labeled as an estimate
everywhere it appears. **This is the single most important recommendation in
this paper**: fix the Ship Date ingestion pipeline and re-run the same
modeling code on real dates — nothing else in this pipeline needs to change.

We similarly found no shipping-cost field in the data (only `Sales`, `Cost`,
`Gross Profit`, which reflect production economics). We proxy shipping cost
as **$0.001 per mile per unit**, an illustrative rate that should be
recalibrated against Nassau's actual freight invoices before being used in
financial planning.

## 4. Exploratory Findings

| Factory | Avg. distance (mi) | Avg. est. lead time (days) | Orders | Avg. margin % |
|---|---:|---:|---:|---:|
| Lot's O' Nuts (AZ) | 1,313 | 6.15 | 5,692 | 69.2% |
| Wicked Choccy's (GA) | 1,166 | 5.90 | 4,152 | 65.1% |
| Sugar Shack (MN) | 1,099 | 5.83 | 33 | 53.2% |
| The Other Factory (TN) | 1,000 | 5.33 | 100 | 10.5% |
| Secret Factory (IL) | 870 | 5.04 | 217 | 51.5% |

Regionally, **Atlantic** orders travel farthest on average (1,458 mi) and
have the longest estimated lead time (6.43 days); **Interior** orders are
shortest (1,021 mi, 5.63 days). The two Wonka Bar factories (Lot's O' Nuts in
Arizona, Wicked Choccy's in Georgia) carry 96% of volume between them but sit
far from the Pacific and Gulf/Atlantic customer bases respectively —
exactly the mismatch the brief describes ("a West Coast order shipped from an
Arizona factory when a closer option exists").

The Other Factory's average margin (10.5%) is sharply lower than every other
factory (>50% elsewhere) — worth a separate cost-structure review outside
this project's scope, since it is driven by production economics (Sales/Cost)
rather than logistics.

## 5. Predictive Modeling

**Features:** shipping distance, units, sales value, product, factory,
region, ship mode, division. **Target:** estimated lead time (days).
**Split:** 80/20 train/test, random_state=42.

| Model | RMSE (days) | MAE (days) | R² |
|---|---:|---:|---:|
| **Linear Regression** | **0.304** | **0.241** | **0.972** |
| Gradient Boosting | 0.311 | 0.245 | 0.970 |
| Random Forest | 0.328 | 0.259 | 0.967 |

Linear Regression was selected (lowest RMSE) — expected, since the estimate
target is close to linear in distance plus categorical offsets by
construction. All three models agree closely, which is itself a useful
sanity check. **Once real Ship Date data is available, this comparison
should be re-run**, since a genuine operational lead-time signal may be more
non-linear (e.g. carrier cutoffs, regional hub congestion) and could favor
Random Forest or Gradient Boosting.

## 6. Scenario Simulation & Recommendations

For every (Product × Region) combination with historical orders, we
simulated shipping from all 5 factories and compared each candidate against
the current assignment on three KPIs: lead-time reduction %, profit impact
per order, and a confidence score (scaled by historical order count, capped
at 500 orders for full confidence).

**Top recommendations (by combined speed + profit + confidence score):**

| Product | Region | Current → Recommended | Orders | Lead time | Profit/order |
|---|---|---|---:|---|---:|
| Wonka Bar – Milk Chocolate | Pacific | Wicked Choccy's → Lot's O' Nuts | 666 | 8.63 → 5.43 days (−37.1%) | +$6.48 |
| Wonka Bar – Triple Dazzle Caramel | Pacific | Wicked Choccy's → Lot's O' Nuts | 676 | 8.68 → 5.50 days (−36.6%) | +$6.10 |
| Wonka Bar – Fudge Mallows | Gulf | Lot's O' Nuts → Wicked Choccy's | 291 | 7.71 → 4.70 days (−39.0%) | +$5.60 |
| Wonka Bar – Nutty Crunch Surprise | Gulf | Lot's O' Nuts → Wicked Choccy's | 296 | 7.68 → 4.74 days (−38.3%) | +$5.41 |
| Wonka Bar – Nutty Crunch Surprise | Atlantic | Lot's O' Nuts → Wicked Choccy's | 490 | 8.45 → 5.81 days (−31.2%) | +$5.01 |

Across all 53 product-region routes, **42 have a reassignment option that
improves both speed and profit simultaneously** (no trade-off needed),
covering 7,069 historical orders, an order-weighted average lead-time
reduction of **27.3%**, and an estimated profit uplift of **~$28,500** across
those orders under our shipping-cost assumption. The clearest, highest-volume
pattern: the two chocolate factories are each shipping a meaningful share of
their volume to the region the *other* factory is better positioned for
(Wicked Choccy's → Pacific; Lot's O' Nuts → Gulf/Atlantic) — cross-shipping
that a two-factory swap for those specific regions would resolve without any
new factory investment.

## 7. Risk Notes

- Recommendations for low-volume products (Sugar Shack's 5 SKUs, Hair
  Toffee, etc.) rest on fewer than 10 historical orders each and carry a
  confidence score below 0.3 — directional only.
- A minority of recommendations trade profit for speed (higher distance-based
  shipping cost in exchange for a faster lead time); these are flagged
  separately in the dashboard's Risk & Impact panel rather than folded into
  the main ranking.
- All dollar figures depend on the $0.001/mile/unit shipping-cost assumption
  and should be treated as directional pending real freight-cost data.

## 8. Recommendation to Leadership

1. **Immediate, no-regret fix:** re-route the two Pacific-region and two
   Gulf/Atlantic-region SKU-region pairs identified above — highest volume,
   unambiguous win on both speed and profit.
2. **Data pipeline fix:** correct Ship Date generation/ingestion and re-run
   this pipeline (code unchanged) to replace the estimated lead-time model
   with one built on real shipping history.
3. **Cost data:** capture actual freight cost per order to replace the
   $0.001/mile/unit proxy with real figures.
4. **Monitor low-confidence SKUs** as their order volume grows before acting
   on their specific recommendations.
