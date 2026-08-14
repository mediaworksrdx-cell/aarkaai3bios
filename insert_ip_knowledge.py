import sys
import os

# Ensure the parent directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_NAME
import modules.rag as rag

print("Loading embedding model:", EMBEDDING_MODEL_NAME)
_st_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
embed_fn = lambda text: _st_model.encode(text, normalize_embeddings=True)

# Initialize RAG engine
rag.init(embed_fn)

topic = "Top 100 most frequent IP addresses from 5 billion log entries under 2 GB RAM limit"
content = """To find the top 100 most frequent IP addresses from a massive log file of 5 billion entries with only 2 GB of RAM available, a naive in-memory hash map/dictionary approach will fail because storing all unique IP addresses and their frequencies in memory would exceed the RAM limit. 

### Why Naive In-Memory Hash Maps Fail
An IPv4 address requires 4 bytes. If there are 100 million unique IP addresses, an in-memory dictionary tracking `{ip: count}` would require several gigabytes. In languages like Python, overhead makes each entry much larger (typically 100-200 bytes per key-value pair), leading to 10-20 GB of memory usage.

### The Correct Solution: Disk-Based Partitioning & Aggregation (MapReduce Approach)
This is solved using an external divide-and-conquer strategy (External Merge Sort or MapReduce partition-by-hash logic):

1. **Step 1: Partitioning (Map):**
   - Read the large log file sequentially (streaming line-by-line).
   - For each log entry, extract the IP address.
   - Hash the IP address and partition it into one of N smaller files on disk (e.g., N = 128 or 256) using a formula like `partition_id = hash(ip) % N`.
   - Write the IP address to the corresponding partition file `partition_x.txt`.
   - **Crucial Property:** The same IP address will always end up in the exact same partition file, while the overall set of unique IPs is distributed roughly equally across the N files.

2. **Step 2: Local Aggregation (Reduce):**
   - Process each of the N partition files one by one.
   - For each partition file, load it into memory and build a local hash map of `IP -> frequency`. Since each partition contains at most `1 / N` of the total unique IPs, the hash map easily fits well within the 2 GB RAM limit.
   - Maintain a min-heap of size 100 to keep track of the top 100 most frequent IPs in the current partition.
   - Save these local top 100 IPs and their frequencies to a temporary file.

3. **Step 3: Global Aggregation:**
   - Combine the local top 100 candidates from all N partition files. This results in at most `100 * N` candidate records (e.g., 25,600 records for N = 256), which easily fits in a few kilobytes of RAM.
   - Aggregate the frequencies of any duplicate IPs across partitions (though by design, each IP is isolated to one partition, so there won't be duplicates across partitions if the hash function is consistent).
   - Sort the combined candidates by frequency and select the top 100 most frequent IP addresses.

### Python Code Example (Partitioned Approach)
```python
import hashlib
import os
import heapq
from collections import defaultdict

NUM_PARTITIONS = 128

def partition_phase(log_file_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    # Open all partition files for writing
    partition_files = {
        i: open(os.path.join(output_dir, f"part_{i}.txt"), "w")
        for i in range(NUM_PARTITIONS)
    }
    
    with open(log_file_path, "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 1:
                ip = parts[0]
                # Determine partition using hash of the IP address
                part_idx = int(hashlib.md5(ip.encode()).hexdigest(), 16) % NUM_PARTITIONS
                partition_files[part_idx].write(ip + "\n")
                
    # Close all files
    for f in partition_files.values():
        f.close()

def aggregate_phase(output_dir):
    candidates = []
    
    for i in range(NUM_PARTITIONS):
        part_path = os.path.join(output_dir, f"part_{i}.txt")
        if not os.path.exists(part_path):
            continue
            
        # Local frequency count for this partition (fits in 2 GB RAM)
        ip_counts = defaultdict(int)
        with open(part_path, "r") as f:
            for line in f:
                ip = line.strip()
                if ip:
                    ip_counts[ip] += 1
                    
        # Find local top 100 in this partition using min-heap
        local_top = heapq.nlargest(100, ip_counts.items(), key=lambda x: x[1])
        candidates.extend(local_top)
        
        # Clean up partition file to save disk space
        os.remove(part_path)
        
    # Global merge: sort all partition candidates
    # (Since hash partitions isolate IPs, no IP appears in multiple partitions)
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[:100]

def find_top_100_ips(log_file_path, temp_dir=\"./temp_partitions\"):
    partition_phase(log_file_path, temp_dir)
    top_100 = aggregate_phase(temp_dir)
    return top_100
```
"""

print("Storing knowledge...")
rag.store_knowledge(topic=topic, content=content, source="system")
print("Done!")
