# Nexus Pipeline: System Capability Analysis

## Current Infrastructure Capacity

### Lambda Functions
- **Pipeline Lambda**: 512MB memory, 60s timeout
- **API Lambda**: 256MB memory, 30s timeout
- **Max file size**: ~6MB (Lambda 15MB limit, but 60s timeout limits processing time)

### Worker Capacity (ECS Fargate)
- **CPU**: 2 vCPU per task
- **Memory**: 8GB RAM per task
- **Timeout**: No timeout (Fargate has no execution time limit)
- **Max file size**: Limited by S3 upload limits (5TB)

### Database
- **PostgreSQL**: db.t3.micro (1 vCPU, 1GB RAM)
- **Storage**: 20GB allocated
- **Throughput**: ~500-1000 IOPS (gp3 storage)

### Storage
- **S3 Data Bucket**: No size limits (practical: TB-scale)
- **DynamoDB**: PAY_PER_REQUEST billing (scalable to millions of requests)

## Maximum Capability Estimates

### File Processing
| Component | Maximum Capacity | Practical Limit |
|-----------|----------------|-----------------|
| **Single File** | 5TB (S3 limit) | 10-100GB (depends on complexity) |
| **Concurrent Files** | 100+ (Lambda concurrency) | 10-20 (API Gateway throttling) |
| **Daily Volume** | 1000+ files | 100-200 files (API rate limits) |

### Throughput Performance
- **Pipeline Lambda**: ~1-2 files/minute (AI mapping + metadata extraction)
- **Worker**: ~5-10 files/minute (8GB RAM, 2vCPU)
- **Database Load**: ~1000 rows/second (PostgreSQL t3.micro)
- **Total Daily Capacity**: ~5000-10000 files/day

### Scalability Limits
- **Lambda Concurrency**: 1000 (account limit, configurable)
- **ECS Tasks**: 10-20 (Fargate cluster size)
- **RDS Connections**: 100 (t3.micro limit)
- **DynamoDB Read/Write**: 40K/20K (on-demand)

## Bottlenecks & Limitations

### Primary Bottlenecks
1. **Bedrock API Rate Limits**: ~10-20 calls/minute (Claude model)
2. **PostgreSQL IOPS**: 500-1000 (t3.micro bottleneck)
3. **API Gateway Throttling**: 1000 requests/second (adjustable)
4. **Lambda Cold Starts**: ~100-500ms per invocation

### Memory Constraints
- **Pipeline Lambda**: 512MB may be insufficient for complex CSV/JSON parsing
- **Worker**: 8GB RAM for large file processing (optimal for 1-10GB files)
- **Database**: 1GB RAM limits concurrent connections and query performance

## Performance Recommendations

### Immediate Improvements
1. **Increase Pipeline Lambda Memory**: 1024MB → 2048MB for complex file parsing
2. **Add Connection Pooling**: In worker to reduce PostgreSQL connection overhead
3. **Implement Batch Processing**: Group small files to reduce Bedrock API calls
4. **Add Monitoring**: CloudWatch alarms for resource utilization

### Scaling Strategies
1. **Auto-Scaling Worker Tasks**: Based on SQS queue depth
2. **Read Replicas**: For PostgreSQL to handle reporting queries
3. **Bedrock Model Selection**: Use faster models (Haiku) for simple mappings
4. **Caching Optimization**: Redis cache for frequent schema lookups

### Capacity Enhancements
| Enhancement | Cost Impact | Performance Gain |
|-------------|-------------|-----------------|
| **r5.large Worker** | +$100/mo | 2x CPU, 16GB RAM |
| **gp3 IOPS Increase** | +$30/mo | 3x database throughput |
| **Provisioned DynamoDB** | +$50/mo | Consistent 10K read/write |
| **Bedrock Model Upgrade** | +$100/mo | Faster response times |

## Future Capacity Planning

### High-Volume Scenario (100K files/day)
- **Worker Cluster**: 5-10 Fargate tasks
- **RDS Upgrade**: db.r5.large (2vCPU, 16GB RAM)
- **DynamoDB Provisioned**: 50K read/write capacity
- **Estimated Cost**: +$300-500/mo

### Enterprise Scenario (1M files/day)
- **Lambda Concurrency**: 5000 (request limit increase)
- **ECS Cluster**: Multiple availability zones
- **Database**: Aurora Serverless (auto-scaling)
- **Bedrock**: Dedicated capacity (enterprise tier)

## Monitoring & Alerting

### Key Metrics to Monitor
- **Lambda Error Rates**: >5% triggers investigation
- **Worker Memory Utilization**: >80% triggers scaling
- **Database Connections**: >80% triggers optimization
- **Bedrock API Latency**: >10s triggers model switch

### Auto-Scaling Triggers
- **SQS Queue Depth**: >100 messages → add worker task
- **Lambda Throttles**: >10% → increase concurrency
- **Database CPU**: >80% → scale up or add replica

## Conclusion

The current infrastructure can handle **5,000-10,000 files/day** with optimal performance. For higher volumes, implement auto-scaling and database optimizations. The primary constraints are Bedrock API limits and PostgreSQL performance, which can be mitigated through caching and architectural improvements.