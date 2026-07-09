import pandas as pd

FILE_PATH = "../IOS_Master_Tracker_Filled_13_Final.xlsx"

try:
    df = pd.read_excel(FILE_PATH, sheet_name="Master Universe")
    
    # 1. Check Target Allocation % and Position Size
    print("--- Target Allocation & Position Size ---")
    problem_companies = ["TITAN.NS", "TEJASNET.NS", "ACMESOLAR.NS", "MHRIL.NS", "CREDITACC.NS"]
    
    for ticker in problem_companies:
        row = df[df["Ticker"] == ticker]
        if not row.empty:
            alloc = row["Target Allocation %"].values[0]
            pos = row["Position Size (₹)"].values[0]
            print(f"{ticker}: Allocation={alloc}, Position={pos}")
            
    # 2. Check Risk Scores
    print("\n--- Risk Scores ---")
    risk_companies = ["SBIN.NS", "TITAN.NS", "PFC.NS", "MHRIL.NS", "CREDITACC.NS"]
    
    for ticker in risk_companies:
        row = df[df["Ticker"] == ticker]
        if not row.empty:
            risk = row["Risk Score (Engine)"].values[0]
            print(f"{ticker}: Risk Score={risk}")
            
    # 3. Check New Columns
    print("\n--- New Columns ---")
    new_cols = [
        "Gross NPA %", "Net NPA %", "CAR %", "PCR %", 
        "Business Risk", "Financial Risk", "Valuation Risk", "Governance Risk", "Total Risk"
    ]
    
    missing = [c for c in new_cols if c not in df.columns]
    if missing:
        print(f"MISSING COLUMNS: {missing}")
    else:
        print(f"All {len(new_cols)} new columns are present.")
        
except Exception as e:
    print(f"Error: {e}")
