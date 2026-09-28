# Executive Summary
### Factory Reallocation & Shipping Optimization — Nassau Candy Distributor

**Bottom line:** Two of our five factories are shipping meaningful volume to
regions the *other* factory is geographically better positioned to serve.
Rebalancing just the highest-volume routes cuts estimated lead time by
roughly a third and improves margin — with no new factory investment.

## What we found

- Products are locked to factories by legacy rules that predate current
  order volumes and geography.
- **Wicked Choccy's (Georgia)** ships a large share of Pacific-region
  chocolate orders that **Lot's O' Nuts (Arizona)** is far closer to.
- **Lot's O' Nuts (Arizona)** ships a large share of Gulf/Atlantic orders
  that **Wicked Choccy's (Georgia)** or **Secret Factory (Illinois)** is
  closer to.
- Across 53 product-region combinations analyzed, **42 have a reassignment
  that improves both delivery speed and profit at the same time** — no
  trade-off required.

## Headline numbers

| Metric | Value |
|---|---|
| Orders covered by "win-win" reassignments | 7,069 |
| Average lead-time reduction on those orders | 27.3% |
| Estimated profit uplift on those orders | ~$28,500 |
| Single largest opportunity | Wonka Bar – Milk Chocolate, Pacific region: 666 orders, −37% lead time, +$6.48/order |

*(Profit figures use an illustrative $0.001/mile/unit shipping-cost estimate,
since the source data has no freight-cost field — treat as directional until
validated against real freight invoices.)*

## One important caveat

The dataset's shipment-date field turned out to be unreliable — timestamps
are years off from when they should be, which appears to be a data-export
issue rather than real shipping history. We built a transparent, distance-
and-ship-mode-based estimate to stand in for it so this analysis could move
forward, and labeled every number that depends on it. **Recommendation:**
have IT/data engineering correct the shipment-date export; the analysis
pipeline built here can then be re-run unchanged on real dates for higher
confidence.

## What's delivered

1. **Interactive dashboard** — select any product/region, see predicted
   lead time by factory, run side-by-side what-if comparisons, and browse
   ranked recommendations with an adjustable speed-vs-profit priority slider.
2. **Research paper** — full methodology, model comparison, and findings.
3. **This summary.**

## Suggested next step

Pilot the two highest-volume reassignments (Milk Chocolate & Triple Dazzle
Caramel → Pacific via Lot's O' Nuts) for one quarter, track actual delivery
times against the model's estimate, and use that real data to validate the
approach before wider rollout.
