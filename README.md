# Nexus: AI-Powered Flexible ETL Pipeline

## The Problem

Every data source has different column names:
- Partner A sends `cust_name`, Partner B sends `customer_name`, Partner C sends `Name`
- Same data, different schemas

Current ETL requires manual mapping for each source. That's not scalable.

## The Solution

Use AI to automatically:
1. **Detect column mismatch** - Map `cust_name` → `customer_name` → `full_name`
2. **Generate transform spec** - Rules for type conversion, formatting, etc.
3. **Execute ETL** - Apply mapping + transforms, load to PostgreSQL

## Architecture

```
┌─────────────────┐     ┌─────────────┐     ┌─────────────┐
│  Upload to S3    │────▶│  Pipeline  │────▶│ DynamoDB  │
│  (products/,    │     │  Lambda   │     │  (jobs)   │
│   customers/)   │     │  (AI map) │     │          │
└─────────────────┘     └─────────────┘     └─────────────┘
                                               │
                     ┌─────────────┐            │
                     │  Frontend  │◀───────────┤
                     │  (approve) │            ▼
                     └─────────────┘     ┌───────────┐
                                      │  Worker  │
                                      │  Lambda  │
                                      └───────────┘
                                            │
                                            ▼
                                     ┌───────────┐
                                     │ PostgreSQL│
                                     │  (data)  │
                                     └───────────┘
```

## Project Structure

```
nexus-pipeline/
├── backend/              # Lambda functions
│   ├── pipeline/       # S3 trigger + AI mapping
│   │   ├── handler.py
│   │   ├── bedrock.py
│   │   └── requirements.txt
│   │
│   ├── worker/        # ETL execution
│   │   ├── handler.py
│   │   ├── extract.py
│   │   ├── transform.py
│   │   ├── load.py
│   │   └── requirements.txt
│   │
│   ├── api/           # Dashboard REST API
│   │   └── handler.py
│   └── tests/         # Unit tests
│
├── frontend/           # Vue 3 approval UI
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   └── stores/
│   └── package.json
│
├── infra/             # SAM template
│   └── template.yaml
│
└── schemas/          # SQL schema files
    └── sql/
        ├── 001_products.sql
        ├── 002_customers.sql
        ├── 003_orders.sql
        └── 004_inventory.sql
```

## Current Status

### Phase 1: Database Schema ✅ DONE
- `schemas/sql/001_products.sql` - products table
- `schemas/sql/002_customers.sql` - customers table
- `schemas/sql/003_orders.sql` - orders table
- `schemas/sql/004_inventory.sql` - inventory table

### Phase 2: Pipeline Lambda ✅ DONE
- `backend/pipeline/handler.py` - S3 event handling, topic detection
- `backend/pipeline/bedrock.py` - AI column mapping (Bedrock)

### Phase 3: Worker Lambda ✅ DONE
- `backend/worker/handler.py` - ETL job execution
- `backend/worker/extract.py` - CSV/JSON parsing
- `backend/worker/transform.py` - Column mapping + transforms
- `backend/worker/load.py` - PostgreSQL insert
- Unit tests (26 transform, 10 extract, 3 handler)

### Phase 4: Infrastructure ✅ DONE
- `infra/template.yaml` - SAM template with:
  - DynamoDB jobs table
  - S3 data bucket
  - Pipeline Lambda (S3 trigger)
  - Worker Lambda (EventBridge trigger)
  - API Lambda + API Gateway + API key
  - Dashboard S3 + CloudFront
  - RDS PostgreSQL
  - VPC with public/private subnets

### Phase 5: Dashboard ✅ DONE
- Vue 3 approval UI with:
  - Job list with status filters
  - Job detail modal with mapping display
  - Approve/reject buttons
  - Auto-refresh

## API Endpoints

| Method | Endpoint | Description |
|-------|----------|-------------|
| GET | `/jobs?status=` | List jobs |
| GET | `/jobs/{jobId}` | Get job details |
| POST | `/jobs/{jobId}/approve` | Approve + trigger ETL |
| POST | `/jobs/{jobId}/reject` | Reject job |

## Data Topic to Table Mapping

| S3 Folder | Target Table | Key Column |
|-----------|-------------|-----------|
| products/ | products | sku |
| customers/ | customers | customer_code |
| orders/ | orders | order_id |
| inventory/ | inventory | sku |

## Deployment

1. Deploy infrastructure:
```bash
cd infra
sam deploy --template-file template.yaml --stack-name nexus-pipeline \
  --parameter-overrides Environment=dev DatabasePassword=<password>
```

2. Build frontend:
```bash
cd frontend
npm install
npm run build
# Upload dist/ files to S3 bucket (from CloudFormation output)
```

## Local Development

### Backend Tests
```bash
cd backend/pipeline && python -m pytest tests/ -v
cd backend/worker && python -m pytest tests/ -v
```

### Frontend
```bash
cd frontend
cp .env.example .env
# Edit .env with API values from CloudFormation output
npm install
npm run dev
```

## Environment Variables

### Pipeline Lambda
- `DYNAMO_TABLE` - DynamoDB table name
- `BEDROCK_MODEL` - Bedrock model ID (default: anthropic.claude-3-haiku-20240307-v1:0)

### Worker Lambda
- `DYNAMO_TABLE` - DynamoDB table name

### API Lambda
- `DYNAMO_TABLE` - DynamoDB table name

### Frontend
- `VITE_API_URL` - API endpoint (from CloudFormation output)
- `VITE_API_KEY` - API key (from CloudFormation output)

## Job Status State Machine

```
uploaded → analyzing → pending_approval → approved → processing → completed
                                           ↘ (rejected) → failed
```

## Transform Rules Reference

| Rule | Input | Output |
|------|-------|--------|
| `transform: uppercase` | "john" | "JOHN" |
| `transform: lowercase` | "JOHN" | "john" |
| `transform: titlecase` | "john doe" | "John Doe" |
| `format: YYYY-MM-DD` | "01/15/2024" | "2024-01-15" |
| `type: boolean` | "yes" | True |
| `type: boolean` | "no" | False |
| `type: number` | "123.45" | 123.45 |
| `mask: ###-####` | "5551234" | "555-1234" |
| `default: N/A` | null | "N/A" |

## CloudFormation Outputs

After deployment, get these from stack outputs:
- `DataBucket` - S3 bucket for uploads
- `JobsTable` - DynamoDB table
- `ApiEndpoint` - Dashboard API URL
- `ApiKeyValue` - API key
- `DashboardUrl` - Frontend URL