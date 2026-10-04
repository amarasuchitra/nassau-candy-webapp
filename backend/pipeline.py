"""End-to-end pipeline: raw CSV -> cleaned data -> EDA -> model -> simulation ->
recommendations -> dashboard bundle.

Run it whenever the source CSV changes or you want to retrain:

    python -m backend.pipeline            # full run (includes EDA charts)
    python -m backend.pipeline --bundle   # only rebuild the dashboard bundle
"""
import argparse
import os
import time

import joblib

from . import config
from .bundle import build_bundle, write_bundle


def _step(name):
    print(f"  • {name}...", flush=True)
    return time.perf_counter()


def run_pipeline(include_eda: bool = True) -> dict:
    import data_prep  # type: ignore
    import modeling  # type: ignore
    import simulate  # type: ignore

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    started = time.perf_counter()
    print("Running Nassau Candy pipeline")

    _step("Cleaning data & engineering features")
    df = data_prep.load_and_clean(config.DATA_PATH)
    df.to_csv(os.path.join(config.OUTPUT_DIR, "processed_data.csv"), index=False)

    if include_eda:
        import eda  # type: ignore
        _step("Exploratory analysis & charts")
        eda.run_eda()

    _step("Training & comparing models")
    results, best_name, _ = modeling.train_all()
    # all_models.joblib is a large by-product nothing else uses
    extra = os.path.join(config.OUTPUT_DIR, "all_models.joblib")
    if os.path.exists(extra):
        os.remove(extra)

    _step(f"Simulating reassignments with {best_name}")
    model = joblib.load(config.MODEL_PATH)
    sim = simulate.simulate_reassignments(df, model)
    sim.to_csv(os.path.join(config.OUTPUT_DIR, "simulation_all_scenarios.csv"), index=False)
    rec = simulate.rank_recommendations(sim)
    rec.to_csv(os.path.join(config.OUTPUT_DIR, "recommendations_ranked.csv"), index=False)
    rec[rec["lead_time_reduction_pct"] > 0].to_csv(
        os.path.join(config.OUTPUT_DIR, "recommendations_actionable.csv"), index=False)

    _step("Building dashboard data")
    bundle = build_bundle(model, df)
    write_bundle(bundle)

    print(f"Done in {time.perf_counter() - started:.1f}s - best model: {best_name}")
    return {"best_model": best_name, "results": results,
            "recommendations": int(len(rec)), "generated_at": bundle["meta"]["generated_at"]}


def rebuild_bundle_only() -> dict:
    model = joblib.load(config.MODEL_PATH)
    bundle = build_bundle(model)
    write_bundle(bundle)
    return {"generated_at": bundle["meta"]["generated_at"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bundle", action="store_true", help="only rebuild the dashboard bundle from existing outputs")
    parser.add_argument("--skip-eda", action="store_true", help="skip EDA charts (faster)")
    args = parser.parse_args()
    if args.bundle:
        print(rebuild_bundle_only())
    else:
        run_pipeline(include_eda=not args.skip_eda)
