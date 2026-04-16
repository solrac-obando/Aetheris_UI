import json
import os
import numpy as np

DATA_PATH = os.path.join(os.path.dirname(__file__), 'gestne_data.json')

def load_gestne_data():
    """Reads the extracted JSON and cleans NaN values for the physics engine."""
    if not os.path.exists(DATA_PATH):
        print(f"Error: No se encontró el archivo de datos en {DATA_PATH}")
        return []
        
    with open(DATA_PATH, 'r') as f:
        raw_data = json.load(f)
        
    cleaned_data = []
    for record in raw_data:
        # We focus on records that have a cluster assignment and basic metrics
        cluster_id = record.get("Cluster_Cuantitativo")
        if cluster_id is None or np.isnan(cluster_id):
            continue
            
        # Handle NaNs for physical mapping
        # Medians as fallback for missing data
        imc = record.get("IMC")
        if imc is None or np.isnan(imc):
            imc = 28.5 # Appx population median
            
        insu = record.get("Insu basal")
        if insu is None or np.isnan(insu):
            # Infer from cluster if IMC is available? Better a stable default
            insu = 12.0 if cluster_id == 1 else 8.0 
            
        shbg = record.get("SHBG")
        if shbg is None or np.isnan(shbg):
            shbg = 40.0
            
        cleaned_record = {
            "id": record.get("Unnamed: 0", "Unknown"),
            "cluster": int(cluster_id), # 1: Metabolic?, 2: Reproductive?
            "imc": float(imc),
            "insu": float(insu),
            "shbg": float(shbg),
            "lh": float(record.get("LH", 5.5) if not np.isnan(record.get("LH", 0)) else 5.5),
            "fsh": float(record.get("FSH", 5.0) if not np.isnan(record.get("FSH", 0)) else 5.0),
            # Metadata for labels
            "raw": record 
        }
        cleaned_data.append(cleaned_record)
        
    print(f"Loader: Propagados {len(cleaned_data)} registros válidos para simulación.")
    return cleaned_data

if __name__ == "__main__":
    data = load_gestne_data()
    print(f"Sample: {data[0]}")
