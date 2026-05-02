## 📁 File Structure
```
drc-verification-dashboard/
├── app.py # Main Streamlit dashboard
├── DRC_Parser.py # Standalone DRC .rpt file parser
├── simulate_drc_runs.py # ECO run simulator (generates test .rpt files)
├── requirements.txt # Python dependencies
├── README.md # Project documentation
└── .gitignore # Ignores duplicate/temp files
```
## Methodology: Predictive DRC Convergence & Triage

This project addresses a critical bottleneck in the ASIC design cycle: the manual, iterative nature of Physical Verification (PV) sign-off. Instead of treating DRC reports as static snapshots, this tool treats them as a **dynamic time-series**, allowing for data-driven tape-out forecasting.

### 1. Automated Report Parsing & Layer Triage
The tool utilizes a modular Python-based parser designed to ingest raw `.rpt` or `.db` files from industry-standard PV suites. It extracts violation counts and categorizes them by:
* **Layer Severity:** Prioritizing critical base layers (Poly, Diffusion, Fin) over metal/via routing.
* **Violation Density:** Identifying "hotspots" where manual ECOs may be inefficient compared to automated router fixes.



### 2. Convergence Forecasting via Linear Regression
The core of the methodology is the **Convergence Slope Analysis**. By tracking violation counts across multiple ECO runs, the tool applies an **Ordinary Least Squares (OLS)** linear regression model to predict the "Zero-Violation" intercept.

The model minimizes the sum of squared residuals:

$$S = \sum_{i=1}^{n} (y_i - (mx_i + b))^2$$

* **Intercept ($b$):** Represents the initial design complexity and rule-set density.
* **Slope ($m$):** Quantifies the team's "fix rate" efficiency.
* **Predicted Intercept ($x$ when $y=0$):** Provides a mathematical forecast for tape-out readiness.



### 3. Scalability & IP Security
* **Synthetic Data Simulation:** To demonstrate logic without exposing proprietary GDSII data, the dashboard includes a synthetic data generator that simulates realistic violation decay curves.
* **Extensible Framework:** The architecture is designed to be "PDK-agnostic," allowing it to be integrated into existing CAD infrastructures for FinFET, BiCMOS, or Planar nodes.

### Built With
* **Python** (NumPy, Pandas)
* **Streamlit** (Web Interface)
* **Scikit-Learn** (Predictive Modeling)

## 🚀 How to Run

### 1. Clone the repo
git clone https://github.com/hrcprasad/drc-verification-dashboard.git
cd drc-verification-dashboard

### 2. Install dependencies
pip install -r requirements.txt

### 3. Launch the dashboard
streamlit run app.py

### 4. Generate test data (optional)
python simulate_drc_runs.py 5 Files/
# Creates 5 simulated ECO run .rpt files in the Files/ folder

## 🔧 Tech Stack
- Python 3.12
- Streamlit
- Plotly
- Pandas
- NumPy (linear regression for convergence prediction)
