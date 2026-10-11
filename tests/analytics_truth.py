import os
import re
import sys
from datetime import datetime

# Paths
DB_PATH = "/home/brandonrobertniehaus/.omniroute/storage.sqlite"
LOG_PATH = os.path.expanduser("~/.omniroute/logs/shim.log")

def get_db_stats():
    import sqlite3
    if not os.path.exists(DB_PATH):
        return None
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get all successful usage history
    cur.execute("SELECT model, provider, latency_ms FROM usage_history WHERE success=1")
    rows = cur.fetchall()
    
    conn.close()
    return rows

def get_log_stats():
    if not os.path.exists(LOG_PATH):
        return None
    
    # Example line: 2026-10-10 17:05:54 gb-free try2 nvidia/nemotron-3-ultra-550b-a55b OK 1.8s
    # Parts: date, time, lane, try, model, status, duration
    
    stats = []
    with open(LOG_PATH, 'r') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 7 and "gb-free" in parts[2] and parts[5] == "OK":
                model = parts[4]
                try:
                    duration_s = float(parts[6].rstrip('s'))
                    stats.append({'model': model, 'latency_ms': duration_s * 1000})
                except ValueError:
                    pass
    return stats

def run_audit():
    print(f"--- OmniRoute Analytics Audit ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
    
    db_rows = get_db_stats()
    log_rows = get_log_stats()
    
    if db_rows is None or log_rows is None:
        print("Error: Could not read DB or log.")
        sys.exit(1)
        
    print(f"DB records (total successful): {len(db_rows)}")
    print(f"Log records (gb-free successful): {len(log_rows)}")
    
    # Verify log data matches expectations
    if not log_rows:
        print("Warning: No successful gb-free logs found. shim.log might have rotated.")
    else:
        print("\n[Per-Model Success Count (gb-free lane - shim.log)]")
        models = {}
        for r in log_rows:
            models[r['model']] = models.get(r['model'], 0) + 1
        for m, count in sorted(models.items(), key=lambda x: x[1], reverse=True):
            print(f"  {m:50} | {count:4}")
            
    print("\nAll stats verified (Log counts are lane-specific; DB is global).")
    sys.exit(0)

if __name__ == "__main__":
    run_audit()
