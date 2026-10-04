# Factory Reallocation and Shipping Optimization for Nassau Candy Distributor

Nassau Candy ships 15 products from 5 factories to 4 regions, and every product is tied to one factory no matter where the customer is. This project works out, for each product and region, which factory should ship it so that delivery is faster without losing profit.

**Live dashboard:** https://candy-factory-allocation.streamlit.app

## What I did

1. Cleaned 10,194 orders and estimated the shipping distance for each one (haversine distance from factory to the customer's state).
2. Trained three models to predict delivery lead time and kept the best one.
3. Simulated every product, region, factory and ship mode combination (1,060 scenarios).
4. Ranked the possible factory changes by time saved, profit impact and how much data supports them.
5. Added a switching cost: a move is only recommended if its yearly saving pays back the one-time cost of moving within 12 months.
6. Grouped the routes with k-means clustering to show where the gains are.
7. Built a dashboard with an animated shipment map so the result can be explored without code.

## Results

| Model | R2 | MAE (days) |
|---|---|---|
| Linear Regression (used) | 0.972 | 0.24 |
| Gradient Boosting | 0.970 | 0.25 |
| Random Forest | 0.967 | 0.26 |

- With a switching cost of $1,500 per route and a 12 month payback limit, 10 routes should be reallocated, 3 should be piloted first and 40 should stay as they are.
- The 10 recommended moves save about $24,599 a year and pay back in 4 to 12 months.
- K-means (k = 4) separates the long-distance, high-gain routes from the rest. All 8 of those routes pass the payback test.

## Project structure

```
data/            the order data (CSV)
src/             data preparation, EDA, modelling, simulation, route analysis
backend/         pipeline that runs everything and builds the dashboard data
outputs/         trained model, summary tables, charts, recommendations
web/             the dashboard (HTML, CSS, JavaScript)
streamlit_app/   Streamlit entry point that serves the dashboard
```

## Run it

```bash
pip install -r requirements.txt
streamlit run streamlit_app/app.py
```

To rebuild everything from the raw data (clean, train, simulate, rank, rebuild the dashboard data):

```bash
python -m backend.pipeline
```

To rerun the route clustering and payback analysis:

```bash
python src/route_analysis.py web/data/dashboard_bundle.json 4
```

## Notes on the data

- The dataset has no factory, distance or shipping cost column. The product to factory mapping and the factory locations come from the project brief, and customers are placed at the centre of their state.
- Shipping cost is estimated at $0.001 per mile per unit. It is a stand-in until real freight costs are available.
- Five chocolate products make up about 97% of the orders. Recommendations for the low-volume products are marked as low confidence in the dashboard.

## Author

Amara Suchitra, Department of AIML, Sai Vidya Institute of Technology, Bengaluru
