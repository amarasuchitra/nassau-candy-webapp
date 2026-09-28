"""Business logic behind the API.

Every calculation here mirrors the dashboard's own logic exactly (web/index.html),
so the API and the page always agree. Nothing here changes the model,
the pipeline or the recommendation logic in src/.
"""
import json
import os
import threading
from collections import defaultdict

import joblib
import pandas as pd

from . import config
from constants import (  # type: ignore
    AVG_TRANSIT_SPEED_MILES_PER_DAY, DIVISION_HANDLING_DAYS, FACTORY_COORDS,
    MIN_LEAD_TIME_DAYS, REGION_COORDS, SHIP_COST_PER_MILE_PER_UNIT, SHIP_MODE_BASE_DAYS,
)
from data_prep import haversine_miles  # type: ignore


class NotFound(ValueError):
    """Unknown product / region / factory / ship mode."""


class AppState:
    """Loads the model + dashboard bundle once and answers API questions."""

    def __init__(self):
        self._lock = threading.Lock()
        self.model = None
        self.bundle = None
        self.load()

    # ------------------------------------------------------------------ load
    def load(self):
        with self._lock:
            self.model = self._load_model()
            self.bundle = self._load_bundle()
            self._index()

    def _load_model(self):
        try:
            return joblib.load(config.MODEL_PATH)
        except Exception as exc:  # missing file or scikit-learn version mismatch
            print(f"Model could not be loaded ({exc!r}); retraining from source data...")
            from .pipeline import run_pipeline
            run_pipeline(include_eda=False)
            return joblib.load(config.MODEL_PATH)

    def _load_bundle(self):
        if os.path.exists(config.BUNDLE_PATH):
            with open(config.BUNDLE_PATH, encoding="utf-8") as fh:
                return json.load(fh)
        from .bundle import build_bundle, write_bundle
        bundle = build_bundle(self.model)
        write_bundle(bundle)
        return bundle

    def _index(self):
        b = self.bundle
        self.sim = b["dashboard_data"]
        self.recs = b["recommendations"]
        self.products = sorted({r["product"] for r in self.sim})
        self.regions = sorted({r["region"] for r in self.sim})
        self.factories = sorted({r["factory"] for r in self.sim})
        self.ship_modes = sorted({r["ship_mode"] for r in self.sim})
        self.current_factory = {}
        self.division = {}
        for r in self.sim:
            self.division.setdefault(r["product"], r["division"])
            if r["is_current"]:
                self.current_factory.setdefault(r["product"], r["factory"])
        self.by_key = defaultdict(list)
        for r in self.sim:
            self.by_key[(r["product"], r["region"], r["ship_mode"])].append(r)

    def reload(self):
        self.load()

    # ------------------------------------------------------------- helpers
    def _check(self, product=None, region=None, factory=None, ship_mode=None):
        for value, allowed, label in ((product, self.products, "product"), (region, self.regions, "region"),
                                      (factory, self.factories, "factory"), (ship_mode, self.ship_modes, "ship mode")):
            if value is not None and value not in allowed:
                raise NotFound(f"Unknown {label} '{value}'. Valid options: {', '.join(allowed)}")

    @staticmethod
    def _formula_estimate(factory, region, ship_mode, division):
        """The dashboard's estimate for product/region pairs with no order history."""
        flat, flon = FACTORY_COORDS[factory]
        rlat, rlon = REGION_COORDS[region]
        dist = haversine_miles(flat, flon, rlat, rlon)
        lead = max(MIN_LEAD_TIME_DAYS, SHIP_MODE_BASE_DAYS.get(ship_mode, 4.0)
                   + dist / AVG_TRANSIT_SPEED_MILES_PER_DAY + DIVISION_HANDLING_DAYS.get(division, 0.3))
        return dist, lead, dist * 1 * SHIP_COST_PER_MILE_PER_UNIT

    # ----------------------------------------------------------------- meta
    def meta(self):
        return {
            "products": [{"name": p, "current_factory": self.current_factory.get(p), "division": self.division.get(p)}
                         for p in self.products],
            "regions": self.regions,
            "factories": self.factories,
            "ship_modes": self.ship_modes,
            "model": self.bundle["model_results"],
            "generated_at": self.bundle.get("meta", {}).get("generated_at"),
        }

    def summary(self):
        """Headline numbers shown at the top of the dashboard."""
        total_orders = sum(f["orders"] for f in self.bundle["factory_summary"])
        best = {}
        for r in self.recs:
            key = (r["Product Name"], r["Region"])
            if key not in best or r["lead_time_reduction_pct"] > best[key]["lead_time_reduction_pct"]:
                best[key] = r
        win = [r for r in best.values() if r["lead_time_reduction_pct"] > 0 and r["profit_impact_per_order"] > 0]
        return {
            "orders_analyzed": total_orders,
            "win_win_routes": len(win),
            "estimated_profit_uplift": round(sum(r["profit_impact_per_order"] * r["orders_affected"] for r in win), 2),
        }

    # ------------------------------------------------------------ simulate
    def simulate(self, product, region, ship_mode="Standard Class"):
        self._check(product=product, region=region, ship_mode=ship_mode)
        current_factory = self.current_factory.get(product, self.factories[0])
        division = self.division.get(product, "Other")
        hist = {r["factory"]: r for r in self.by_key.get((product, region, ship_mode), [])}
        rows = []
        for f in self.factories:
            h = hist.get(f)
            if h:
                rows.append({"factory": f, "is_current": h["is_current"], "distance_miles": h["distance"],
                             "lead_time_days": h["lead_time"], "ship_cost_per_order": h["ship_cost"],
                             "orders": h["orders"], "estimated": False})
            else:
                dist, lead, cost = self._formula_estimate(f, region, ship_mode, division)
                rows.append({"factory": f, "is_current": f == current_factory, "distance_miles": round(dist, 1),
                             "lead_time_days": round(lead, 2), "ship_cost_per_order": round(cost, 3),
                             "orders": 0, "estimated": True})
        rows.sort(key=lambda r: r["lead_time_days"])
        current = next((r for r in rows if r["is_current"]), rows[0])
        best = rows[0]
        saved = current["lead_time_days"] - best["lead_time_days"]
        return {
            "product": product, "region": region, "ship_mode": ship_mode,
            "current_factory": current["factory"],
            "recommended_factory": best["factory"],
            "already_optimal": best["factory"] == current["factory"],
            "days_faster": round(saved, 2),
            "pct_faster": round(saved / current["lead_time_days"] * 100, 1) if current["lead_time_days"] else 0.0,
            "miles_saved": round(current["distance_miles"] - best["distance_miles"], 1),
            "cost_change_per_order": round(best["ship_cost_per_order"] - current["ship_cost_per_order"], 3),
            "ranking": rows,
        }

    # ------------------------------------------------------------- predict
    def predict(self, product, region, factory, ship_mode, units=None, sales=None):
        """Live prediction from the trained model for any factory choice."""
        self._check(product=product, region=region, factory=factory, ship_mode=ship_mode)
        division = self.division.get(product, "Other")
        prof = next((r for r in self.sim if r["product"] == product and r["region"] == region
                     and r["factory"] == factory), None)
        if prof:
            dist = prof["distance"]
        else:
            flat, flon = FACTORY_COORDS[factory]
            dist = haversine_miles(flat, flon, *REGION_COORDS[region])
        avg_units, avg_sales = self._order_averages(product, region)
        units = float(units) if units is not None else avg_units
        sales = float(sales) if sales is not None else avg_sales
        X = pd.DataFrame([{
            "shipping_distance_miles": dist, "Units": units, "Sales": sales,
            "Product Name": product, "Current Factory": factory, "Region": region,
            "Ship Mode": ship_mode, "Division": division,
        }])
        lead = float(self.model.predict(X)[0])
        return {
            "product": product, "region": region, "factory": factory, "ship_mode": ship_mode,
            "units": units, "sales": sales, "distance_miles": round(dist, 1),
            "predicted_lead_time_days": round(max(lead, MIN_LEAD_TIME_DAYS), 2),
            "est_shipping_cost": round(dist * units * SHIP_COST_PER_MILE_PER_UNIT, 3),
            "model": self.bundle["model_results"].get("best_model"),
        }

    def _order_averages(self, product, region):
        """Average units and order value for this product (and region when it has
        history) — the same averages the simulation feeds the model."""
        if not hasattr(self, "_avg_cache"):
            try:
                df = pd.read_csv(os.path.join(config.OUTPUT_DIR, "processed_data.csv"),
                                 usecols=["Product Name", "Region", "Units", "Sales"])
                self._avg_cache = (df.groupby(["Product Name", "Region"])[["Units", "Sales"]].mean().to_dict("index"),
                                   df.groupby("Product Name")[["Units", "Sales"]].mean().to_dict("index"))
            except Exception:
                self._avg_cache = ({}, {})
        by_pair, by_product = self._avg_cache
        row = by_pair.get((product, region)) or by_product.get(product) or {"Units": 1.0, "Sales": 10.0}
        return float(row["Units"]), float(row["Sales"])

    # ------------------------------------------------------------- compare
    def compare(self, product, candidate):
        """Current factory vs a candidate, Standard Class, weighted by orders."""
        self._check(product=product, factory=candidate)
        current = self.current_factory[product]
        prod_rows = [r for r in self.sim if r["product"] == product and r["ship_mode"] == "Standard Class"]
        regions = sorted({r["region"] for r in prod_rows})
        detail = []
        for region in regions:
            for scenario, factory in (("Current", current), ("Candidate", candidate)):
                row = next((r for r in prod_rows if r["region"] == region and r["factory"] == factory), None)
                if row:
                    detail.append({"region": region, "scenario": scenario, "factory": factory,
                                   "orders": row["orders"], "distance_miles": row["distance"],
                                   "lead_time_days": row["lead_time"], "ship_cost_per_order": row["ship_cost"]})

        def wavg(rows, key):
            w = sum(r["orders"] for r in rows) or 1
            return sum(r[key] * r["orders"] for r in rows) / w

        cur = [d for d in detail if d["scenario"] == "Current"]
        cand = [d for d in detail if d["scenario"] == "Candidate"]
        lt_cur, lt_cand = wavg(cur, "lead_time_days"), wavg(cand, "lead_time_days")
        cost_cur, cost_cand = wavg(cur, "ship_cost_per_order"), wavg(cand, "ship_cost_per_order")
        return {
            "product": product, "current_factory": current, "candidate_factory": candidate,
            "current_lead_time_days": round(lt_cur, 3), "candidate_lead_time_days": round(lt_cand, 3),
            "lead_time_change_days": round(lt_cand - lt_cur, 3),
            "lead_time_change_pct": round(-(lt_cand - lt_cur) / lt_cur * 100, 2) if lt_cur else 0.0,
            "current_ship_cost": round(cost_cur, 3), "candidate_ship_cost": round(cost_cand, 3),
            "ship_cost_change": round(cost_cand - cost_cur, 3),
            "orders_affected": sum(d["orders"] for d in cur),
            "candidate_is_faster": lt_cand < lt_cur,
            "by_region": detail,
        }

    # ----------------------------------------------------- recommendations
    def recommendations(self, regions=None, min_orders=0, priority=0.5, limit=30):
        regions = regions or self.regions
        for r in regions:
            self._check(region=r)
        rows = [dict(r) for r in self.recs if r["Region"] in regions and r["orders_affected"] >= min_orders]
        for r in rows:
            r["priority_score"] = (max(r["lead_time_reduction_pct"], 0) * priority
                                   + r["profit_impact_per_order"] * 20 * (1 - priority))
        rows.sort(key=lambda r: r["priority_score"], reverse=True)
        return {"total": len(rows), "items": rows[:limit]}

    def top_opportunities(self, n=3):
        best = {}
        for r in self.recs:
            key = (r["Product Name"], r["Region"])
            if key not in best or r["composite_score"] > best[key]["composite_score"]:
                best[key] = r
        top = sorted(best.values(), key=lambda r: r["composite_score"], reverse=True)[:n]
        return [{
            "rank": i + 1,
            "product": r["Product Name"], "region": r["Region"],
            "move_from": r["current_factory"], "move_to": r["recommended_factory"],
            "days_faster": round(r["current_lead_time_days"] - r["new_lead_time_days"], 2),
            "lead_time_reduction_pct": r["lead_time_reduction_pct"],
            "orders_affected": r["orders_affected"],
            "estimated_impact": round(r["profit_impact_per_order"] * r["orders_affected"], 2),
        } for i, r in enumerate(top)]

    # ----------------------------------------------------------------- risk
    def risk(self, limit=15):
        risky = sorted((r for r in self.recs if r["profit_impact_per_order"] < 0 and r["lead_time_reduction_pct"] > 0),
                       key=lambda r: r["profit_impact_per_order"])
        low = sorted((r for r in self.recs if r["confidence_score"] < 0.3), key=lambda r: r["confidence_score"])
        return {
            "profit_tradeoffs": {"count": len(risky), "items": risky[:limit]},
            "low_confidence": {"count": len(low), "items": low[:limit]},
        }

