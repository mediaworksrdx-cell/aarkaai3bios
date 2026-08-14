import sys
import os
import re
import json
from collections import Counter

def parse_log_line(line):
    # Expressions régulières pour analyser les formats de log courants (CLF / Combined)
    # Exemple : 127.0.0.1 - - [10/Oct/2000:13:55:36 -0700] "GET /index.html HTTP/1.0" 200 2326
    clf_pattern = re.compile(
        r'^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<date>.*?)\]\s+"(?P<method>\S+)\s+(?P<path>[^\s\?]+).*?"\s+(?P<status>\d+)\s+(?P<size>\S+)'
    )
    
    match = clf_pattern.match(line)
    if match:
        return match.group("ip"), match.group("path")
    
    # Fallback simple si le format est différent (extraction basique)
    parts = line.split()
    if len(parts) >= 7:
        ip = parts[0]
        # Recherche de la méthode HTTP pour localiser l'endpoint
        for i, part in enumerate(parts):
            if part.strip('"') in ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"]:
                if i + 1 < len(parts):
                    path = parts[i + 1].split('?')[0] # Enlever les paramètres de requête
                    return ip, path
    return None, None

def analyze_log(file_path):
    if not os.path.exists(file_path):
        print(json.dumps({"error": f"Le fichier '{file_path}' est introuvable."}, indent=4))
        sys.exit(1)
        
    total_requests = 0
    ips = []
    endpoints = []
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            ip, path = parse_log_line(line)
            if ip and path:
                total_requests += 1
                ips.append(ip)
                endpoints.append(path)
                
    ip_counter = Counter(ips)
    endpoint_counter = Counter(endpoints)
    
    report = {
        "total_requests": total_requests,
        "unique_ips_count": len(ip_counter),
        "top_10_ips": dict(ip_counter.most_common(10)),
        "top_10_endpoints": dict(endpoint_counter.most_common(10))
    }
    
    print(json.dumps(report, indent=4))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <chemin_du_fichier_log>")
        sys.exit(1)
        
    analyze_log(sys.argv[1])
