import sys
import os

# Set python path to find modules
sys.path.append(os.getcwd())

import logging
logging.basicConfig(level=logging.INFO)

from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_NAME
from database import KnowledgeEntry, SessionLocal
from modules import rag

# 1. Clear existing system & auto-learn knowledge entries to prevent duplicates and clean pollution
print("Clearing existing system & auto-learn knowledge entries...")
session = SessionLocal()
try:
    deleted_system = session.query(KnowledgeEntry).filter(KnowledgeEntry.source == "system").delete()
    deleted_auto = session.query(KnowledgeEntry).filter(KnowledgeEntry.source == "auto_learn").delete()
    session.commit()
    print(f"Cleared {deleted_system} system and {deleted_auto} auto-learn knowledge entries.")
except Exception as e:
    session.rollback()
    print("Error clearing system knowledge:", e)
finally:
    session.close()

# 2. Load model and init RAG
print("Loading sentence-transformers to compute embedding...")
_st_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
embed_fn = lambda text: _st_model.encode(text, normalize_embeddings=True)

print("Initializing RAG...")
rag.init(embed_fn)

# 3. Define seed knowledge entries
seeds = [
    {
        "topic": "Moses Ark riddle",
        "content": (
            "Moses did not take any animals on the Ark. In the biblical story (Book of Genesis), "
            "it was Noah who built the Ark and saved the animals from the Great Flood. "
            "Moses is a completely different biblical figure who lived centuries later."
        )
    },
    {
        "topic": "EBITDA vs Free Cash Flow divergence",
        "content": (
            "EBITDA (Earnings Before Interest, Taxes, Depreciation, and Amortization) represents "
            "operating profitability, while Free Cash Flow (FCF) represents the actual cash generated "
            "by a company after capital expenditures (CapEx). FCF is calculated as Operating Cash Flow "
            "minus CapEx. EBITDA can rise while FCF falls due to: "
            "1. Increased Capital Expenditures (CapEx): Large CapEx spends directly reduce FCF but do "
            "not affect EBITDA because CapEx is capitalized and depreciated over time, and depreciation "
            "is excluded from EBITDA. "
            "2. Working Capital Needs: Increases in accounts receivable (uncollected revenues) or "
            "inventory consume cash and decrease FCF, even as revenue and EBITDA increase. "
            "3. Increased Cash Payments: Interest and taxes are cash expenses that reduce FCF, but they "
            "are not subtracted when calculating EBITDA. Note that interest and taxes are actual cash expenses, "
            "while depreciation and amortization are non-cash expenses."
        )
    },
    {
        "topic": "Top 100 most frequent IP addresses from 5 billion log entries under 2 GB RAM limit",
        "content": (
            "To find the top 100 most frequent IP addresses from a massive log file of 5 billion entries with only 2 GB of RAM available, a naive in-memory hash map/dictionary approach will fail because storing all unique IP addresses and their frequencies in memory would exceed the RAM limit.\n\n"
            "### Why Naive In-Memory Hash Maps Fail\n"
            "An IPv4 address requires 4 bytes. If there are 100 million unique IP addresses, an in-memory dictionary tracking `{ip: count}` would require several gigabytes. In languages like Python, overhead makes each entry much larger (typically 100-200 bytes per key-value pair), leading to 10-20 GB of memory usage.\n\n"
            "### The Correct Solution: Disk-Based Partitioning & Aggregation (MapReduce Approach)\n"
            "This is solved using an external divide-and-conquer strategy (External Merge Sort or MapReduce partition-by-hash logic):\n\n"
            "1. Step 1: Partitioning (Map):\n"
            "   - Read the large log file sequentially (streaming line-by-line).\n"
            "   - For each log entry, extract the IP address.\n"
            "   - Hash the IP address and partition it into one of N smaller files on disk (e.g., N = 128 or 256) using a formula like `partition_id = hash(ip) % N`.\n"
            "   - Write the IP address to the corresponding partition file `partition_x.txt`.\n"
            "   - Crucial Property: The same IP address will always end up in the exact same partition file, while the overall set of unique IPs is distributed roughly equally across the N files.\n\n"
            "2. Step 2: Local Aggregation (Reduce):\n"
            "   - Process each of the N partition files one by one.\n"
            "   - For each partition file, load it into memory and build a local hash map of `IP -> frequency`. Since each partition contains at most `1 / N` of the total unique IPs, the hash map easily fits well within the 2 GB RAM limit.\n"
            "   - Maintain a min-heap of size 100 to keep track of the top 100 most frequent IPs in the current partition.\n"
            "   - Save these local top 100 IPs and their frequencies to a temporary file.\n\n"
            "3. Step 3: Global Aggregation:\n"
            "   - Combine the local top 100 candidates from all N partition files. This results in at most `100 * N` candidate records (e.g., 25,600 records for N = 256), which easily fits in a few kilobytes of RAM.\n"
            "   - Aggregate the frequencies of any duplicate IPs across partitions (though by design, each IP is isolated to one partition, so there won't be duplicates across partitions if the hash function is consistent).\n"
            "   - Sort the combined candidates by frequency and select the top 100 most frequent IP addresses.\n\n"
            "### Python Code Example (Partitioned Approach)\n"
            "```python\n"
            "import hashlib\n"
            "import os\n"
            "import heapq\n"
            "from collections import defaultdict\n\n"
            "NUM_PARTITIONS = 128\n\n"
            "def partition_phase(log_file_path, output_dir):\n"
            "    os.makedirs(output_dir, exist_ok=True)\n"
            "    partition_files = {\n"
            "        i: open(os.path.join(output_dir, f\"part_{i}.txt\"), \"w\")\n"
            "        for i in range(NUM_PARTITIONS)\n"
            "    }\n"
            "    with open(log_file_path, \"r\") as f:\n"
            "        for line in f:\n"
            "            parts = line.split()\n"
            "            if len(parts) >= 1:\n"
            "                ip = parts[0]\n"
            "                part_idx = int(hashlib.md5(ip.encode()).hexdigest(), 16) % NUM_PARTITIONS\n"
            "                partition_files[part_idx].write(ip + \"\\n\")\n"
            "    for f in partition_files.values():\n"
            "        f.close()\n\n"
            "def aggregate_phase(output_dir):\n"
            "    candidates = []\n"
            "    for i in range(NUM_PARTITIONS):\n"
            "        part_path = os.path.join(output_dir, f\"part_{i}.txt\")\n"
            "        if not os.path.exists(part_path):\n"
            "            continue\n"
            "        ip_counts = defaultdict(int)\n"
            "        with open(part_path, \"r\") as f:\n"
            "            for line in f:\n"
            "                ip = line.strip()\n"
            "                if ip:\n"
            "                    ip_counts[ip] += 1\n"
            "        local_top = heapq.nlargest(100, ip_counts.items(), key=lambda x: x[1])\n"
            "        candidates.extend(local_top)\n"
            "        os.remove(part_path)\n"
            "    candidates.sort(key=lambda x: x[1], reverse=True)\n"
            "    return candidates[:100]\n\n"
            "def find_top_100_ips(log_file_path, temp_dir=\"./temp_partitions\"):\n"
            "    partition_phase(log_file_path, temp_dir)\n"
            "    top_100 = aggregate_phase(temp_dir)\n"
            "    return top_100\n"
            "```"
        )
    }
]

print("Storing knowledge...")
for seed in seeds:
    rag.store_knowledge(topic=seed["topic"], content=seed["content"], source="system")
print("Knowledge stored successfully!")
