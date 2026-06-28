# Numbers to Know

Reference data for back-of-the-envelope estimation. Think in orders of
magnitude, not decimals. Round to one significant figure. The ratio between
tiers (1x / 10x / 100x) is what shifts an architecture, not the exact values.

---

## Latency Reference Table

| Operation | Latency | Order |
|-----------|---------|-------|
| L1 cache reference | 1 ns | 1 ns |
| L2 cache reference | 4 ns | ~ns |
| L3 cache reference | 10 ns | ~10 ns |
| Main memory reference | 100 ns | ~100 ns |
| SSD random read (4KB) | 100 us | ~100 us |
| HDD random read | 2-10 ms | ~ms |
| Same-datacenter round trip | 0.5 ms | ~ms |
| Redis / Memcached GET | 0.1-0.5 ms | ~sub-ms |
| Read 1 MB from memory | 3 us | ~us |
| Read 1 MB from SSD | 50 us | ~100 us |
| Read 1 MB from HDD | 2 ms | ~ms |
| Read 1 MB from network (1 Gbps) | 10 ms | ~10 ms |
| Cross-region round trip (US East <-> West) | 40-60 ms | ~50 ms |
| Cross-continent round trip (US <-> Europe) | 80-120 ms | ~100 ms |
| TLS handshake | 5-50 ms | ~10 ms |
| DNS lookup (uncached) | 20-100 ms | ~50 ms |

**Key insight**: Memory is ~1000x faster than SSD, SSD is ~100x faster than
HDD, same-DC network is ~100x faster than cross-continent. These ratios
determine when caching pays off and when you must colocate.

---

## Per-Server QPS by Tier

| Tier | Rule of Thumb | Notes |
|------|---------------|-------|
| Single SQL/RDBMS node (indexed point queries) | ~1,000 QPS | Joins, range scans, fat payloads can be 10x worse |
| Single SQL/RDBMS node (simple writes) | ~1,000-5,000 QPS | With WAL, fsync, index updates |
| Key-value store node (Redis, DynamoDB) | ~10,000-100,000 QPS | Depends on value size; Redis single-threaded for commands |
| Cache server (Redis/Memcached, reads) | ~100,000-1,000,000 QPS | Memory-bound; sub-ms latency |
| One modern CPU core (simple requests) | ~1,000 req/s | CPU-bound work: serialize, validate, compute |
| 64-core server (CPU-bound) | ~64,000 req/s | Linear with cores for independent requests |
| Kafka broker (per partition) | ~10,000-100,000 msg/s | Throughput scales with partitions |
| Flink (per task slot) | ~10,000-100,000 events/s | Depends on state size and complexity |

**How to use**: `peak_QPS / per_server_QPS = minimum server count`. If the
result is >100, the architecture needs a fundamentally different approach (not
just more servers).

---

## Powers of 2

| Power | Value | Approx | Common Usage |
|-------|-------|--------|-------------|
| 2^10 | 1,024 | ~1 K | 1 KB |
| 2^16 | 65,536 | ~65 K | TCP port range |
| 2^20 | 1,048,576 | ~1 M | 1 MB |
| 2^30 | 1,073,741,824 | ~1 B | 1 GB |
| 2^32 | 4,294,967,296 | ~4 B | IPv4 address space, 32-bit integer limit |
| 2^40 | | ~1 T | 1 TB |
| 2^48 | | | MAC address space |
| 2^64 | | | Snowflake ID space, 64-bit integer limit |
| 2^128 | | | UUID v4 space |

**Shortcut**: 2^10 ≈ 10^3. So 2^30 ≈ 10^9 (1 billion), 2^40 ≈ 10^12
(1 trillion).

---

## Availability Nines

| Nines | Availability | Downtime/Year | Downtime/Month | Downtime/Week |
|-------|-------------|---------------|----------------|---------------|
| 2 nines | 99% | 3.65 days | 7.3 hours | 1.68 hours |
| 3 nines | 99.9% | 8.76 hours | 43.8 min | 10.1 min |
| 4 nines | 99.99% | 52.6 min | 4.38 min | 1.01 min |
| 5 nines | 99.999% | 5.26 min | 26.3 sec | 6.05 sec |

**How to use**: Choose a target, then work backward to the required
redundancy. 4 nines requires automatic failover (<30s) with no single points
of failure. 5 nines requires multi-region active-active with no planned
downtime for deployments.

**Error budget**: 99.99% = 0.01% failure budget. For 1M req/sec, that is 100
failed requests/sec before the budget is exhausted. If this month's error
budget is consumed, freeze non-critical deploys.

---

## Estimation Recipes

### Recipe 1: DAU to QPS

```
DAU = [number]
Actions per user per day = [number]
Daily requests = DAU × actions

Average QPS = daily_requests / 86,400
  (use 100,000 for easy math: 1 day ≈ 10^5 seconds)

Peak QPS = average_QPS × peak_factor
  (default peak_factor = 2; spiky workloads = 5-10)
```

**Example (YouTube views)**:
```
DAU = 2B
Views per user per day = 35 (70B total / 2B DAU)
Daily views = 70B
Average QPS = 70B / 100K = 700K
Peak QPS = 700K × 2 = 1.4M
```

### Recipe 2: Storage Estimation

```
Writes per day = write_QPS × 86,400
Storage per day = writes_per_day × avg_object_size
Total storage = storage_per_day × retention_days

Watch units: storage is sold in base-10 (GB = 10^9 bytes)
RAM is base-2 (GiB = 2^30 bytes). Close enough for estimates.
```

**Example (YouTube video metadata)**:
```
New videos per day = 1M
Avg metadata size = 1 KB
Storage per day = 1M × 1 KB = 1 GB/day
10-year total = 1 GB × 3,650 = 3.65 TB

(Video files stored separately in blob store: 
 1M × 500 MB avg = 500 PB/day -- different system entirely)
```

### Recipe 3: Bandwidth

```
Read bandwidth = read_QPS × avg_response_size
Write bandwidth = write_QPS × avg_request_size

Egress costs money ($0.01-0.09/GB depending on cloud).
```

**Example**:
```
Read QPS = 100K, avg response = 10 KB
Read bandwidth = 100K × 10 KB = 1 GB/s = 8 Gbps

Monthly egress = 1 GB/s × 86,400 × 30 = 2.6 PB
At $0.05/GB = $130K/month in egress alone
```

### Recipe 4: Server Count

```
Servers needed = peak_QPS / per_server_QPS

Per-server QPS depends on the bottleneck:
  CPU-bound:    ~1K req/s per core → 64K per 64-core server
  Memory-bound: ~100K-1M (cache hit path)
  IO-bound:     ~1K-10K (DB queries)
  Network-bound: limited by NIC (10-25 Gbps typical)
```

### Recipe 5: Working Set / Memory

```
Working set = hot_data_size
  (typically 20% of total data ≈ 80% of requests)

Memory per cache node = 64-256 GB typical
Cache nodes needed = working_set / memory_per_node

Hit rate target: 90%+ (below this, question if the data is cacheable)
```

**Example (video view counts)**:
```
Total videos = 3.6B
Hot set = 20% = 720M videos
Per-entry = 8 bytes (ID) + 8 bytes (count) = 16 bytes
Working set = 720M × 16 = 11.5 GB → fits in one Redis node

Full dataset = 3.6B × 16 = 57.6 GB → fits in one node's memory
```

---

## Quick Estimation Cheat Sheet

| What You Need | Formula |
|---------------|---------|
| Seconds in a day | ~100,000 (86,400 actual) |
| Requests per day from QPS | QPS × 100,000 |
| QPS from daily requests | requests / 100,000 |
| MB/s to Gbps | MB/s × 8 / 1000 |
| Bytes in common units | 1 KB = 10^3, 1 MB = 10^6, 1 GB = 10^9, 1 TB = 10^12 |
| Percentage to count | 1% of 1M = 10K |
| Years to days | 1 year ≈ 365 days, 10 years ≈ 3,650 days |

**Golden rule**: Estimate when the number will change your architecture. Skip
estimation when it will not. If a component handles 100 QPS or 10,000 QPS and
your design is the same either way, the exact number does not matter.
