# DebuggingAgent — Complete 20 Production Queries & Answers

*Aarka AI Technical Reference Encyclopedia*

---

## [Q01] Diagnose and provide the fix for: 'MemoryError: Unable to allocate array with shape (100000, 100000)'.

### Root Cause Analysis & Solution: MemoryError with Huge 2D Arrays

#### 1. Root Cause Analysis
An array with shape `(100000, 100000)` of 64-bit floating-point numbers (`float64`) requires:
$$10^5 \times 10^5 = 10^{10} \text{ elements} \times 8 \text{ bytes} = 80\times 10^9 \text{ bytes} \approx 80\text{ GB}$$
If the host operating system cannot allocate an $80\text{ GB}$ contiguous block of physical RAM, the Python runtime raises `MemoryError`.

#### 2. Production Fixes & Architectural Alternatives
1. **Memory-Mapped Arrays (`np.memmap`):**
   Stores the array on disk (SSD) and maps virtual memory pages into RAM on-demand:
   ```python
   import numpy as np
   
   # Allocate 80 GB array directly on disk without exhausting RAM
   mmap_array = np.memmap('large_matrix.dat', dtype='float64', mode='w+', shape=(100000, 100000))
   mmap_array[0, 0] = 42.0
   mmap_array.flush()
   ```
2. **Sparse Matrices (`scipy.sparse`):**
   If the matrix contains mostly zeros (e.g., correlation matrices, graph adjacency matrices), use Compressed Sparse Row (CSR) format:
   ```python
   import scipy.sparse as sp
   # Allocates memory strictly for non-zero elements
   sparse_mat = sp.csr_matrix((100000, 100000), dtype=np.float32)
   ```
3. **Chunked Processing:** Process data in batches using generator pipelines or Dask/Polars.

---

## [Q02] Fix: 'RecursionError: maximum recursion depth exceeded while calling a Python object' in factorial.

### Root Cause Analysis & Solution: RecursionError in Factorial Computation

#### 1. Root Cause Analysis
Python's default recursion limit is $1,000$ stack frames (`sys.getrecursionlimit()`). A recursive factorial implementation:
```python
def factorial(n):
    return 1 if n <= 1 else n * factorial(n - 1)
```
allocates a new stack frame for each call. When $n > 1000$, Python raises `RecursionError: maximum recursion depth exceeded`.

#### 2. Production Fixes
1. **Iterative Formulation (O(1) Memory Overhead):**
   ```python
   def factorial_iterative(n: int) -> int:
       if n < 0:
           raise ValueError("Factorial is undefined for negative integers.")
       result = 1
       for i in range(2, n + 1):
           result *= i
       return result
   ```
2. **Built-in Optimized Implementation:**
   Always prefer Python's C-accelerated standard library:
   ```python
   import math
   result = math.factorial(n)
   ```

---

## [Q03] Debug: 'KeyError: 'user_id'' when unpacking a webhook request payload in FastAPI.

### Root Cause Analysis & Solution: KeyError: 'user_id' in Webhook Payload

#### 1. Root Cause Analysis
A `KeyError: 'user_id'` occurs when code attempts direct dictionary key indexing (`payload['user_id']`) on an incoming webhook payload where `'user_id'` is either missing, null, or nested under another key (e.g., `payload['data']['user_id']`).

#### 2. Production Fixes
1. **Pydantic Schema Validation (FastAPI Idiomatic):**
   Define an explicit request model with graceful field validation:
   ```python
   from pydantic import BaseModel, Field
   from typing import Optional
   
   class WebhookPayload(BaseModel):
       user_id: str = Field(..., description="Unique customer identifier")
       event_type: str
       metadata: Optional[dict] = Field(default_factory=dict)
   
   @app.post("/webhook")
   async def handle_webhook(payload: WebhookPayload):
       # user_id is guaranteed to exist and be validated
       process_user(payload.user_id)
   ```
2. **Safe Dictionary Retrieval with Error Handling:**
   ```python
   user_id = payload.get("user_id")
   if not user_id:
       raise HTTPException(status_code=400, detail="Missing required 'user_id' in webhook payload.")
   ```

---

## [Q04] Fix: 'TypeError: 'NoneType' object is not subscriptable' occurring during nested dict navigation.

### Root Cause Analysis & Solution: TypeError: 'NoneType' object is not subscriptable

#### 1. Root Cause Analysis
Occurs when traversing nested dictionaries or API responses (e.g., `data['user']['address']['zip']`) where an intermediate key resolves to `None` instead of a dictionary. Attempting to subscript `None['address']` triggers the error.

#### 2. Production Fixes
1. **Chained `.get()` with Default Empty Dictionaries:**
   ```python
   zip_code = (data.get('user') or {}).get('address', {}).get('zip')
   ```
2. **Safe Path Traversal Utility:**
   ```python
   def safe_get(d: dict, *keys, default=None):
       curr = d
       for k in keys:
           if not isinstance(curr, dict):
               return default
           curr = curr.get(k)
           if curr is None:
               return default
       return curr
   
   zip_code = safe_get(data, 'user', 'address', 'zip', default='00000')
   ```

---

## [Q05] Resolve: 'UnboundLocalError: cannot access local variable where it is not associated with a value'.

### Root Cause Analysis & Solution: UnboundLocalError in Variable Scope

#### 1. Root Cause Analysis
```python
count = 10
def increment():
    count += 1  # Raises UnboundLocalError
```
Because `count` is assigned within `increment()`, Python treats `count` as a **local variable** throughout the entire function scope. When evaluating `count += 1`, Python attempts to read the local variable before it has been bound, raising `UnboundLocalError`.

#### 2. Production Fixes
1. **Explicit `global` or `nonlocal` Declaration:**
   ```python
   count = 10
   def increment():
       global count
       count += 1
   ```
2. **Pure Functional Approach (Preferred):**
   Avoid mutating global state by passing parameters and returning values:
   ```python
   def increment(val: int) -> int:
       return val + 1
   ```

---

## [Q06] Diagnose deadlock in multithreading when two threads acquire lock A and lock B in reverse order.

### Root Cause Analysis & Solution: Multithreading Deadlock (Lock Ordering)

#### 1. Root Cause Analysis
A classic dining philosophers deadlock occurs when Thread 1 acquires Lock A and waits for Lock B, while Thread 2 simultaneously acquires Lock B and waits for Lock A:
```text
Thread 1: Acquire(Lock A) ──> Waiting for Lock B
Thread 2: Acquire(Lock B) ──> Waiting for Lock A
```
Both threads block indefinitely, causing application freeze.

#### 2. Production Fixes
1. **Strict Global Lock Hierarchy:**
   Always acquire locks in an invariant, globally consistent alphabetical or numeric order:
   ```python
   import threading
   
   lock_a = threading.Lock()
   lock_b = threading.Lock()
   
   def worker_safe():
       # Both threads must acquire in the exact same order: A then B
       with lock_a:
           with lock_b:
               perform_critical_action()
   ```
2. **Lock Timeout with Backoff:**
   ```python
   acquired = lock_b.acquire(timeout=5.0)
   if not acquired:
       lock_a.release()  # Release held lock to avoid deadlocking peer
       time.sleep(random.uniform(0.1, 0.5))
   ```

---

## [Q07] Fix: 'AttributeError: 'list' object has no attribute 'items'' when looping over JSON payload.

### Root Cause Analysis & Solution: AttributeError: 'list' object has no attribute 'items'

#### 1. Root Cause Analysis
The `.items()` method belongs exclusively to mapping types (dictionaries). This error occurs when the code assumes a JSON payload is a dictionary (`for k, v in payload.items():`), but the API actually returned a JSON array/list (`[{"id": 1}, {"id": 2}]`).

#### 2. Production Fixes
```python
if isinstance(payload, dict):
    for k, v in payload.items():
        process_pair(k, v)
elif isinstance(payload, list):
    for item in payload:
        if isinstance(item, dict):
            process_item(item)
else:
    raise ValueError(f"Expected dict or list, got {type(payload).__name__}")
```

---

## [Q08] Resolve: 'sqlite3.OperationalError: database is locked' in concurrent worker setup.

### Root Cause Analysis & Solution: sqlite3.OperationalError: database is locked

#### 1. Root Cause Analysis
SQLite is a serverless, file-based database. In default `DELETE` journal mode, write operations place an exclusive lock on the entire database file. When multiple threads or processes attempt to write concurrently, subsequent transactions fail with `sqlite3.OperationalError: database is locked`.

#### 2. Production Fixes
1. **Enable Write-Ahead Logging (WAL Mode):**
   WAL mode allows concurrent readers and a writer simultaneously without blocking:
   ```python
   import sqlite3
   
   conn = sqlite3.connect("app.db", timeout=30.0)
   conn.execute("PRAGMA journal_mode=WAL;")
   conn.execute("PRAGMA busy_timeout=5000;")  # Wait up to 5 seconds before error
   ```
2. **Thread-Safe Local Connections:**
   SQLite connections cannot be shared across threads. Use `threading.local()` to maintain one connection per thread (see [`modules/code_specs.py`](file:///c:/Users/daarv/.gemini/antigravity/scratch/aarkaai3b/modules/code_specs.py) `SQLiteConnectionManager`).

---

## [Q09] Debug: 'ZeroDivisionError: float division by zero' in CAGR calculation when initial_value is 0.

### Root Cause Analysis & Solution: ZeroDivisionError in CAGR Calculation

#### 1. Root Cause Analysis
The standard CAGR formula is:
$$\text{CAGR} = \left(\frac{V_{\text{final}}}{V_{\text{initial}}}\right)^{\frac{1}{n}} - 1$$
If $V_{\text{initial}} = 0$, evaluating $V_{\text{final}} / V_{\text{initial}}$ causes a `ZeroDivisionError`. Additionally, if $V_{\text{initial}} < 0$, calculating fractional powers of negative numbers produces invalid complex numbers.

#### 2. Production Fix with Strict Input Guards
```python
def calculate_cagr(initial_value: float, final_value: float, years: float) -> float:
    if initial_value <= 0:
        raise ValueError(f"Initial value must be strictly positive (> 0), got {initial_value}")
    if final_value < 0:
        raise ValueError(f"Final value must be non-negative (>= 0), got {final_value}")
    if years <= 0:
        raise ValueError(f"Duration in years must be strictly positive (> 0), got {years}")
    
    return (final_value / initial_value) ** (1.0 / years) - 1.0
```

---

## [Q10] Fix: 'TypeError: can only concatenate str (not 'int') to str' in logging message format.

### Root Cause Analysis & Solution: TypeError: can only concatenate str (not 'int') to str

#### 1. Root Cause Analysis
In Python, strings cannot be implicitly concatenated with numeric types (`"User count: " + 42` raises `TypeError`).

#### 2. Production Fixes
1. **Formatted String Literals (f-strings — Preferred):**
   ```python
   count = 42
   logger.info(f"User count: {count}")
   ```
2. **Standard Logger Format Specifiers (Avoids Eager Formatting):**
   ```python
   logger.info("User count: %d", count)
   ```

---

## [Q11] Diagnose and fix slow database query caused by missing index on user_id and created_at.

### Root Cause Analysis & Solution: Slow Database Query on user_id and created_at

#### 1. Root Cause Analysis
Running `SELECT * FROM orders WHERE user_id = 'usr_123' ORDER BY created_at DESC;` without a proper index forces the database engine to perform a full sequential table scan (Seq Scan) across millions of rows, followed by an in-memory or disk sort.

#### 2. Production Fix: Composite B-Tree Index
Execute a composite index creation matching query equality and sorting direction:
```sql
CREATE INDEX idx_orders_user_created ON orders (user_id, created_at DESC);
```
* **Performance Impact:** Reduces query execution plan from an $\mathcal{O}(N)$ sequential table scan to an $\mathcal{O}(\log N)$ index range scan with zero additional sort overhead. Verify using `EXPLAIN ANALYZE`.

---

## [Q12] Fix: 'RuntimeError: Set changed size during iteration' in active connection pool cleaner.

### Root Cause Analysis & Solution: RuntimeError: Set changed size during iteration

#### 1. Root Cause Analysis
In Python, modifying a collection (adding or deleting elements) while directly iterating over it invalidates the internal hash table iterator:
```python
for conn in active_connections:
    if conn.is_closed():
        active_connections.remove(conn)  # Raises RuntimeError
```

#### 2. Production Fixes
1. **Iterate Over a Shallow Snapshot Copy:**
   ```python
   for conn in list(active_connections):
       if conn.is_closed():
           active_connections.discard(conn)
   ```
2. **Set Comprehension (Atomic Replacement):**
   ```python
   active_connections = {conn for conn in active_connections if not conn.is_closed()}
   ```

---

## [Q13] Resolve: 'ConnectionRefusedError: [Errno 111] Connection refused' on Redis cache connect.

### Root Cause Analysis & Solution: ConnectionRefusedError: [Errno 111] on Redis Connect

#### 1. Root Cause Analysis
`Errno 111 Connection refused` indicates that the client sent a TCP SYN packet to `host:port` (typically `127.0.0.1:6379`), but the operating system responded with a TCP RST packet because no active process was listening on that port or the firewall blocked the connection.

#### 2. Systematic Troubleshooting Steps
1. **Verify Redis Daemon Status:**
   ```bash
   sudo systemctl status redis-server || sudo systemctl status redis
   ```
   If inactive, restart via `sudo systemctl start redis`.
2. **Check Bind Address & Protected Mode:**
   Inspect `/etc/redis/redis.conf`. If connecting from a remote host, ensure `bind 0.0.0.0` is configured and `protected-mode no` or appropriate `requirepass` authentication is set.
3. **Resilient Client Connection with Connection Pooling:**
   ```python
   import redis
   from redis.retry import Retry
   from redis.backoff import ExponentialBackoff
   
   retry = Retry(ExponentialBackoff(), 3)
   pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0, retry=retry)
   r = redis.Redis(connection_pool=pool, socket_connect_timeout=3.0)
   r.ping()
   ```

---

## [Q14] Debug: 'IndexError: pop from empty list' in FIFO queue processing loop.

### Root Cause Analysis & Solution: IndexError: pop from empty list

#### 1. Root Cause Analysis
Calling `items.pop(0)` or `items.pop()` on a list with length 0 raises `IndexError: pop from empty list`. In concurrent consumer loops, this occurs when multiple workers check `if queue:` simultaneously, but another thread consumes the item before the current thread calls `.pop()`.

#### 2. Production Fixes
1. **Thread-Safe Queue (`queue.Queue`):**
   ```python
   import queue
   task_queue = queue.Queue()
   
   # Blocking get with timeout avoids race conditions
   try:
       item = task_queue.get(timeout=1.0)
       process(item)
       task_queue.task_done()
   except queue.Empty:
       pass
   ```
2. **Double-Checked Locking or deque:**
   Use `collections.deque` with atomic pop operations wrapped in an explicit thread lock.

---

## [Q15] Fix: 'ValueError: time data does not match format' when parsing ISO-8601 UTC timestamps.

### Root Cause Analysis & Solution: ValueError: time data does not match format

#### 1. Root Cause Analysis
Occurs when parsing ISO-8601 timestamps (e.g., `'2026-11-01T10:00:00Z'` or `'2026-11-01T15:30:00.123456+05:30'`) using strict format strings like `strptime(s, "%Y-%m-%dT%H:%M:%S")`, which fail on trailing 'Z', microsecond fractions, or timezone offsets.

#### 2. Production Fix: ISO Parser
In modern Python 3.11+, use the built-in `datetime.fromisoformat()` which handles UTC 'Z' and arbitrary offsets:
```python
from datetime import datetime

ts_str = "2026-11-01T10:00:00Z"
dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
```

---

## [Q16] Diagnose floating point rounding error where 0.1 + 0.2 != 0.3 in financial calculations.

### Root Cause Analysis & Solution: Floating Point Rounding Error (0.1 + 0.2 != 0.3)

#### 1. Root Cause Analysis
Computers represent numbers in IEEE 754 binary floating-point format (base 2). Numbers like $0.1$ and $0.2$ cannot be represented precisely as finite binary fractions:
```python
0.1 = 0.0001100110011001100110011..._2
0.1 + 0.2 = 0.300000000000000044408920985006...
```
Comparing `0.1 + 0.2 == 0.3` evaluates to `False`. In quantitative finance, cumulative floating-point errors create balance sheet reconciliation gaps and incorrect tax calculations.

#### 2. Production Fix: `decimal.Decimal`
Always use fixed-point decimal arithmetic for currency, tax lots, and account balances:
```python
from decimal import Decimal

val1 = Decimal('0.1')
val2 = Decimal('0.2')
total = val1 + val2

assert total == Decimal('0.3')  # Evaluates strictly to True
```

---

## [Q17] Fix: 'PermissionError: [Errno 13] Permission denied' when writing to restricted workspace path.

### Root Cause Analysis & Solution: PermissionError: [Errno 13] Permission denied

#### 1. Root Cause Analysis
A process attempted to create or write to a file in a directory where the process's effective User ID (UID) lacks write permissions (e.g., writing to `/var/log` or the application root when running as unprivileged user `appuser` UID 10001).

#### 2. Production Fix
Redirect output paths to authorized, sandboxed directories configured via environment variables:
```python
import os
import tempfile

safe_dir = os.environ.get("SAFE_WORK_DIR", tempfile.gettempdir())
output_path = os.path.join(safe_dir, "report.pdf")

with open(output_path, "wb") as f:
    f.write(data)
```

---

## [Q18] Resolve circular import error between modules.models and modules.services.

### Root Cause Analysis & Solution: Circular Import in Python Modules

#### 1. Root Cause Analysis
Circular imports occur when `module_a` imports `module_b`, while `module_b` simultaneously imports `module_a`:
```text
module_a.py ──imports──> module_b.py ──imports──> module_a.py (Incomplete Module Object!)
```
When `module_b` attempts to access an attribute from `module_a` before `module_a` has finished executing its top-level definitions, Python raises `ImportError: cannot import name ... from partially initialized module`.

#### 2. Production Fixes
1. **Architectural Separation (Recommended):** Extract shared models, interfaces, or types into a third shared module (`modules/schemas.py` or `modules/types.py`) imported by both.
2. **Type Checking Guard:** If the import is strictly for type annotations:
   ```python
   from typing import TYPE_CHECKING
   if TYPE_CHECKING:
       from modules.services import OrderService
   ```

---

## [Q19] Debug async coroutine 'RuntimeWarning: coroutine was never awaited' in background dispatch.

### Root Cause Analysis & Solution: RuntimeWarning: coroutine was never awaited

#### 1. Root Cause Analysis
In Python's `asyncio`, calling an `async def` function does **not** execute its body; it returns a coroutine object. If the caller fails to `await` the coroutine or schedule it on the event loop:
```python
async def send_alert(): ...
send_alert()  # Fails to execute! Emits RuntimeWarning
```
The coroutine is garbage collected without ever running.

#### 2. Production Fixes
1. **Await the Coroutine in Async Context:**
   ```python
   await send_alert()
   ```
2. **Schedule Background Task on the Event Loop:**
   ```python
   import asyncio
   task = asyncio.create_task(send_alert())
   ```

---

## [Q20] Fix: 'json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)' on empty response.

### Root Cause Analysis & Solution: json.decoder.JSONDecodeError on Empty Response

#### 1. Root Cause Analysis
Calling `response.json()` on an HTTP response whose body is empty (e.g., HTTP `204 No Content`, `200 OK` with zero bytes, or an unexpected network reset) raises `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`.

#### 2. Production Fix
Verify body content and status codes before parsing:
```python
import requests

def safe_parse_json(response: requests.Response) -> dict:
    if response.status_code == 204 or not response.text.strip():
        return {}
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON payload from {response.url}: {response.text[:200]}") from exc
```

---

