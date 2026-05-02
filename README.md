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
