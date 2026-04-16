"""
Aetheris Fraud-Watch 2000 Data Generator.
Generates a SQLite database with 2,000 transaction entries for fraud visualization.
"""
import sqlite3
import os
import random
import json
import time

# Seed for reproducibility
random.seed(42)

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'fraud.db')

# IP addresses and accounts for clustering
LEGIT_IPS = [f"192.168.1.{i}" for i in range(1, 100)]
FRAUD_IPS = [f"45.22.11.{i}" for i in range(1, 10)]
LEGIT_ACCOUNTS = [f"ACC-{random.randint(10000, 99999)}" for _ in range(200)]
FRAUD_ACCOUNTS = [f"FRAUD-ACC-{i}" for i in range(1, 5)]

def generate_fraud_data(count=2000):
    """Generate professional synthetic transaction data."""
    entries = []
    
    for i in range(count):
        is_fraud = random.random() < 0.05  # 5% fraud rate
        
        if is_fraud:
            # Fraudulent transaction: high score, specific IPs/Accounts
            fraud_score = random.uniform(0.7, 1.0)
            amount = random.uniform(500, 5000)
            source_ip = random.choice(FRAUD_IPS)
            target_account = random.choice(FRAUD_ACCOUNTS)
            cluster_id = FRAUD_IPS.index(source_ip)  # Group by IP for attraction
        else:
            # Legitimate transaction: low score, diverse IPs/Accounts
            fraud_score = random.uniform(0.0, 0.3)
            amount = max(10, random.lognormvariate(5, 1.5))
            source_ip = random.choice(LEGIT_IPS)
            target_account = random.choice(LEGIT_ACCOUNTS)
            cluster_id = -1  # No cluster for legitimate
            
        entries.append({
            'id': i + 1,
            'amount': round(amount, 2),
            'fraud_score': round(fraud_score, 3),
            'source_ip': source_ip,
            'target_account': target_account,
            'timestamp': int(time.time()) - random.randint(0, 86400),
            'cluster_id': cluster_id
        })
    
    return entries

def create_database(db_path=None, entries=None):
    """Create the Fraud SQLite database."""
    if db_path is None:
        db_path = DATABASE_PATH
    if entries is None:
        entries = generate_fraud_data(2000)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY,
            amount REAL NOT NULL,
            fraud_score REAL NOT NULL,
            source_ip TEXT NOT NULL,
            target_account TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            cluster_id INTEGER NOT NULL
        )
    """)
    
    for entry in entries:
        cursor.execute("""
            INSERT INTO transactions (id, amount, fraud_score, source_ip, target_account, timestamp, cluster_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entry['id'], entry['amount'], entry['fraud_score'], 
            entry['source_ip'], entry['target_account'], 
            entry['timestamp'], entry['cluster_id']
        ))
    
    conn.commit()
    conn.close()
    
    print(f"Created {db_path} with {len(entries)} entries")
    return db_path

if __name__ == '__main__':
    create_database()
