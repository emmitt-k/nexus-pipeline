# Nexus Pipeline - Infrastructure Visualization

This document visualizes the complete infrastructure using Mermaid.js diagrams.

## Architecture Overview

```mermaid
flowchart TB
    subgraph External["External"]
        Partner["Partner Systems"]
        User["Dashboard Users"]
    end

    subgraph Upload["Upload Layer"]
        S3["S3 Data Bucket"]
        CloudFront["CloudFront CDN"]
        Dashboard["Vue Dashboard"]
    end

    subgraph Pipeline["Pipeline Layer"]
        PipelineLambda["Pipeline Lambda<br/AI Mapping"]
        Bedrock["Bedrock Claude<br/Column Mapping"]
    end

    subgraph Storage["Storage Layer"]
        JobsTable["DynamoDB Jobs"]
        SchemaCache["DynamoDB Schema Cache"]
        SQS["SQS Job Queue"]
    end

    subgraph Backend["Backend API"]
        ApiLambda["API Lambda<br/listJobs, approveJob"]
        ApiGateway["API Gateway<br+ API Key Auth"]
    end

    subgraph Worker["Worker Layer"]
        ECS["ECS Fargate<br/ETL Worker"]
        PostgreSQL["PostgreSQL<br Target Database"]
    end

    Partner -->|Upload CSV/JSON| S3
    S3 -->|Trigger| PipelineLambda
    PipelineLambda -->|AI Mapping| Bedrock
    Bedrock -->|Mapping Result| PipelineLambda
    PipelineLambda -->|Save Job| JobsTable
    PipelineLambda -->|Cache Check| SchemaCache
    SchemaCache -->|Cached Mapping| PipelineLambda

    User -->|HTTPS| CloudFront
    CloudFront -->|Proxy| Dashboard
    Dashboard -->|API Calls| ApiGateway
    ApiGateway -->|Invoke| ApiLambda

    ApiLambda -->|Query Jobs| JobsTable
    ApiLambda -->|Approve to Queue| SQS

    SQS -->|Consume Messages| ECS
    ECS -->|Read from S3| S3
    ECS -->|Transform & Load| PostgreSQL

    JobsTable -->|Status Update| ApiLambda
```

## Data Flow Sequence

```mermaid
sequenceDiagram
    participant P as Partner
    participant S3 as S3 Bucket
    participant PL as Pipeline Lambda
    participant B as Bedrock
    participant DB as DynamoDB
    participant F as Vue Dashboard
    participant API as API Lambda
    participant Q as SQS Queue
    participant W as ECS Worker
    participant PG as PostgreSQL

    Note over P,PL: Step 1: File Upload
    P->>S3: Upload CSV file
    S3->>PL: Trigger (ObjectCreated)

    Note over PL,B: Step 2: AI Mapping
    PL->>B: Get column mapping
    B-->>PL: Return mapping

    Note over PL,DB: Step 3: Job Creation
    PL->>DB: Save job (pending_approval)
    DB-->>PL: Job saved

    Note over F,API: Step 4: Human Review
    F->>API: GET /jobs
    API-->>F: Job list
    F->>API: POST /jobs/{id}/approve

    Note over API,Q: Step 5: Queue Job
    API->>DB: Update status (approved)
    API->>Q: Send message

    Note over Q,W: Step 6: Process
    Q->>W: Trigger worker
    W->>S3: Read file
    W->>W: Transform data
    W->>PG: Load to database

    Note over W,DB: Step 7: Complete
    W->>DB: Update status (completed)
```

## Component Details

### Pipeline Flow

```mermaid
flowchart LR
    subgraph Input["Input"]
        CSV[CSV File]
        JSON[JSON File]
    end

    subgraph Process["Processing"]
        Extract[Extract<br/>Read S3]
        Analyze[Analyze<br/>Detect Columns]
        AI[AI Mapping<br/>Bedrock]
        Cache[Cache Check<br/>DynamoDB]
        Transform[Transform<br/>Apply Mapping]
    end

    subgraph Output["Output"]
        Job[Job Record<br/>DynamoDB]
        Mapping[Schema Mapping<br/>JSON]
    end

    CSV --> Extract
    JSON --> Extract
    Extract --> Analyze
    Analyze --> Cache
    Cache -->|Cache Hit| Transform
    Cache -->|Cache Miss| AI
    AI -->|New Mapping| Transform
    Transform --> Job
    Transform --> Mapping
```

### Worker ETL

```mermaid
flowchart LR
    subgraph Trigger["SQS Trigger"]
        Queue[SQS Queue]
    end

    subgraph ETL["ETL Process"]
        Consume[Consume<br/>Message]
        Get[Get Job<br/>Details]
        Extract[Extract<br/>Read S3]
        Transform[Transform<br/>Apply Rules]
        Load[Load<br/>PostgreSQL]
    end

    subgraph Result["Result"]
        Success[Update Status<br/>completed]
        Error[Update Status<br/>failed]
    end

    Queue --> Consume
    Consume --> Get
    Get --> Extract
    Extract --> Transform
    Transform -->|Success| Load
    Load -->|Success| Success
    Transform -->|Error| Error
```

## Infrastructure Resources

```mermaid
flowchart TB
    subgraph AWS["AWS Cloud"]
        subgraph Compute["Compute"]
            Lambda1[Lambda<br/>Pipeline]
            Lambda2[Lambda<br/>API]
            ECS[ECS Fargate<br/>Worker]
        end

        subgraph Data["Data"]
            Dynamo1[DynamoDB<br/>Jobs]
            Dynamo2[DynamoDB<br/>Schema Cache]
            RDS[PostgreSQL<br/>Target DB]
        end

        subgraph Queue["Queue"]
            SQS[SQS Queue]
        end

        subgraph Network["Network"]
            VPC[VPC 10.0.0.0/16]
            PublicSubnet[Public Subnets]
            PrivateSubnet[Private Subnets]
        end

        subgraph Storage["Storage"]
            S3B[S3 Bucket<br/>Data]
            S3D[S3 Bucket<br/>Dashboard]
        end

        subgraph CDN["CDN"]
            CF[CloudFront]
        end

        subgraph API["API"]
            APIGW[API Gateway]
        end

        subgraph AI["AI"]
            Bedrock[Amazon Bedrock<br/>Claude]
        end
    end
```

## Security Boundaries

```mermaid
flowchart TB
    subgraph Public["Public Zone"]
        Users[Users]
        CDN_Entry[CloudFront Entry]
    end

    subgraph VPC_Public["VPC - Public Subnets"]
        APIGW[API Gateway]
        Lambda_API[Lambda API]
    end

    subgraph VPC_Private["VPC - Private Subnets"]
        Lambda_Pipeline[Lambda Pipeline]
        ECS_Task[ECS Fargate Task]
        RDS[PostgreSQL]
    end

    subgraph Managed["AWS Managed"]
        S3[S3 Buckets]
        Dynamo[DynamoDB Tables]
        SQS[SQS Queue]
        Bedrock[Amazon Bedrock]
    end

    Users -->|HTTPS| CDN_Entry
    CDN_Entry -->|Proxy| S3
    APIGW -->|Auth| Lambda_API
    Lambda_API --> Dynamo
    Lambda_Pipeline -->|Read/Write| S3
    Lambda_Pipeline -->|AI Call| Bedrock
    Lambda_Pipeline --> Dynamo
    ECS_Task -->|Read| S3
    ECS_Task -->|Write| RDS
    Lambda_API -->|Send| SQS
    ECS_Task -->|Consume| SQS
```

## Cost Breakdown

```mermaid
pie title Monthly Cost (Estimated)
    "ECS Fargate (Worker)" : 100
    "Bedrock AI" : 110
    "RDS PostgreSQL" : 30
    "Pipeline Lambda" : 20
    "DynamoDB" : 20
    "API Lambda" : 10
    "CloudFront + S3" : 18
```

## Status Flow

```mermaid
stateDiagram-v2
    [*] --> Uploaded
    Uploaded --> Pending_Approval : Job Created
    Pending_Approval --> Approved : User Approves
    Pending_Approval --> Rejected : User Rejects
    Approved --> Queued : Sent to SQS
    Queued --> Processing : Worker Picks Up
    Processing --> Completed : Success
    Processing --> Failed : Error
    Completed --> [*]
    Failed --> [*]
    Rejected --> [*]
```