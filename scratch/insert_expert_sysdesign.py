import os
import sys

# Ensure modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_NAME
from modules import rag

# Initialize embedding function
print("Loading sentence transformer model for indexing...")
_st_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device="cpu")
embed_fn = lambda text: _st_model.encode(text, normalize_embeddings=True)

# Initialize RAG
print("Initializing RAG collection...")
rag.init(embed_fn)

topic = "System Design: Distributed URL Shortener Service Architecture Best Practices"
content = """# Distributed URL Shortener Service (e.g., TinyURL) Design Best Practices

## 1. System Requirements & Capacity Estimation
When estimating capacity for a URL shortener designed for 100 million new URLs per day:
- **Write Request Volume:** 100M URLs / 86400 seconds ≈ 1,160 writes/sec (Peak Write RPS ≈ 2,300).
- **Read Request Volume:** Assuming a 10:1 read-to-write ratio: 1 billion reads/day ≈ 11,600 reads/sec (Peak Read RPS ≈ 23,000).
- **URL Record Storage Size (Not 20KB!):**
  - `id` (Unique Long ID / Snowflake): 8 bytes
  - `short_code` (Base62 encoded key): 7-8 bytes (represents 62^7 = 3.5 trillion URLs)
  - `original_url` (long destination URL): 200-500 bytes (average 300 bytes)
  - `user_id`: 16 bytes
  - `created_at` / `expired_at` (timestamps): 16 bytes
  - Total record size ≈ 350-500 bytes.
- **Storage Growth:** 100 million URLs/day * 500 bytes ≈ 50 GB per day (1.5 TB per month, 18 TB per year).
- **Bandwidth:**
  - Incoming (Writes): 1,160 writes/sec * 500 bytes ≈ 580 KB/s.
  - Outgoing (Reads): 11,600 reads/sec * 500 bytes ≈ 5.8 MB/s.
- **Cache Hit Ratio & Memory Requirement:**
  - Standard Pareto principle (80/20 rule): Cache 20% of the daily read traffic.
  - 20% of 1 billion reads = 200 million reads/day.
  - Cache size: 200M entries * 500 bytes ≈ 100 GB RAM required for the Redis cluster (utilizing LRU eviction policy).

## 2. Core Hash & ID Generation Algorithm (Why Hashing Fails)
- **Why simple Hashing fails:** Generating a hash (MD5 or SHA-256) of the long URL and taking the first 6-7 characters creates high probability of collisions. Checking the database for collisions on every write creates a database bottleneck.
- **The Correct Solution (Distributed Unique IDs + Base62):**
  - Use a distributed unique ID generator (e.g., **Twitter Snowflake** or an auto-incrementing key in a coordinated database cluster) to generate a unique 64-bit integer.
  - Convert this unique 64-bit integer into a string using **Base62 encoding** (using characters `[a-zA-Z0-9]`).
  - Example: An integer ID like `2009215674938` encodes to `a9B8c` (exactly 5-7 characters).
  - This guarantees absolute uniqueness without database collision checks (O(1) time complexity for writes).

## 3. Database Schema & Storage Choice
- **Table Structure:**
  ```sql
  CREATE TABLE requests (
      id BIGINT PRIMARY KEY,
      short_code VARCHAR(10) UNIQUE NOT NULL,
      original_url TEXT NOT NULL,
      user_id VARCHAR(64),
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```
- **Storage Choice:** Because a URL shortener is a simple key-value lookup (`short_code -> original_url`), wide-column NoSQL databases like **Cassandra** or key-value stores like **DynamoDB** scale infinitely better for read-heavy operations than traditional relational databases.

## 4. Redirect Flow & Caching
- **Redirect Mechanism:**
  - Use **HTTP 302 (Found / Temporary Redirect)** if click tracking, statistics, and user analytics (geo-location, device, referrers) are required. Browsers do not cache 302 redirects, forcing every click to hit the server.
  - Use **HTTP 301 (Moved Permanently)** if minimizing server load is the absolute priority, as browsers will cache the redirect locally.
- **Request Flow:**
  - Client makes `GET /short_code` request.
  - API Gateway routes request.
  - Check **Redis** cache:
    - **Hit:** Return HTTP 302 redirect directly to the client (O(1) latency).
    - **Miss:** Query the database (DynamoDB/Cassandra). If found, write to Redis cache, then return HTTP 302 redirect. If not found, return HTTP 404.

## 5. Analytics & Scalable Click Counters (Why click++ fails)
- **The Scaling Problem:** Performing an inline SQL `UPDATE requests SET clicks = clicks + 1 WHERE short_code = 'xyz'` on every read request creates write lock contention on the database, crashing the service under high read volume.
- **The Correct Solution:**
  - When a redirect occurs, write a click tracking event message asynchronously to a **Kafka** topic.
  - A consumer service reads messages from Kafka in batches.
  - The consumer batches and aggregates click statistics in-memory.
  - Every 1-5 minutes, perform a batch database update or store the statistics in a separate time-series database.

## 6. System Bottlenecks & Failure Mitigation
- **Hotspots (Celebrity URLs):** When a single short URL goes viral, it hits a single partition in Redis or DynamoDB. Solve by using local caching on the application servers and partitioning DynamoDB by a composite key (e.g., `short_code + random_salt`).
- **Cache Stampede:** Occurs when a highly popular cache key expires and concurrent requests all query the database simultaneously. Solve by using mutual exclusion locks (mutex) or background pre-fetching.
- **Multi-Region Replication:** Deploy API servers globally and replicate data across regions (US, EU, APAC) using multi-master replication to ensure low read latency worldwide.
"""

print("Storing expert knowledge...")
rag.store_knowledge(topic=topic, content=content, source="architecture")
print("Expert system design guidelines stored successfully!")
