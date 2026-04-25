import os
import sys
import pandas as pd
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def extract_tables_from_pdf(pdf_path):
    print(f"Extracting tables from PDF: {pdf_path}")
    try:
        import pdfplumber
    except ImportError:
        print("ERROR: pdfplumber not installed. Cannot parse PDF.")
        return None
        
    extracted_dfs = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if table and len(table) > 1:
                    raw_cols = table[0]
                    clean_cols = []
                    seen = set()
                    for c in raw_cols:
                        c_str = str(c).strip() if c else "Unnamed"
                        c_str = c_str.replace('\n', ' ')
                        new_c = c_str
                        i = 1
                        while new_c in seen:
                            new_c = f"{c_str}_{i}"
                            i += 1
                        seen.add(new_c)
                        clean_cols.append(new_c)
                        
                    df = pd.DataFrame(table[1:], columns=clean_cols)
                    extracted_dfs.append(df)
                    
    if not extracted_dfs:
        print("No tables found in PDF.")
        return None
        
    master_df = pd.concat(extracted_dfs, ignore_index=True)
    return master_df

def normalize_columns(df):
    df.columns = [str(c).lower().strip().replace(' ', '_').replace('\n', '') for c in df.columns]
    mapping = {
        'data': 'date',
        'turbidity': 'study_turbidity_ntu',
        'turbiditate': 'study_turbidity_ntu',
        'nitrate': 'nitrate_mgl',
        'nitrati': 'nitrate_mgl',
        'nitrite': 'nitrite_mgl',
        'ammonium': 'ammonium_mgl',
        'iron': 'iron_mgl',
        'sulfate': 'sulfate_mgl',
        'calcium': 'calcium_mgl',
        'magnesium': 'magnesium_mgl',
        'ph': 'ph',
        'conductivity': 'conductivity',
        'temperature': 'temperature_c',
        'dissolved_oxygen': 'dissolved_oxygen_mgl'
    }
    df.rename(columns=mapping, inplace=True)
    return df

def clean_and_validate(df):
    if 'date' not in df.columns:
        print("WARNING: No 'date' column found.")
        return None
        
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    
    wq_params = ['study_turbidity_ntu', 'nitrate_mgl', 'ammonium_mgl', 'ph', 'temperature_c']
    found_params = [p for p in wq_params if p in df.columns]
    
    if not found_params:
        print("WARNING: No recognized water quality parameters found in the file.")
        
    for col in df.columns:
        if col != 'date':
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    df['source'] = 'study'
    df['location'] = 'Tarnita'
    return df

def process_study_file(file_path):
    os.makedirs(config.PROCESSED_DIR, exist_ok=True)
    os.makedirs(config.RAW_DIR, exist_ok=True)
    
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        return None
        
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.csv':
        df = pd.read_csv(file_path)
    elif ext == '.pdf':
        df = extract_tables_from_pdf(file_path)
        if df is not None:
            df.to_csv(os.path.join(config.RAW_DIR, "study_extracted.csv"), index=False)
    else:
        print("ERROR: Unsupported file extension.")
        return None
        
    if df is None or df.empty:
        return None
        
    df = normalize_columns(df)
    df_clean = clean_and_validate(df)
    
    if df_clean is not None:
        out_path = os.path.join(config.PROCESSED_DIR, "study_clean.csv")
        df_clean.to_csv(out_path, index=False)
        print(f"Successfully saved cleaned study data to {out_path}")
        return out_path
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--study", type=str, required=True)
    args = parser.parse_args()
    process_study_file(args.study)
