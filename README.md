
## BudgetRAG — Visually Grounded Retrieval-Augmented Generation Project on AWS

BudgetRAG is a Retrieval-Augmented Generation (RAG) system designed to answer questions over large, complex documents (e.g. 500+ page government budgets) while providing visual, document-level grounding for each answer.

Instead of returning text-only citations, the system surfaces cropped image references from the original document pages that directly support each response, improving trust, auditability, and interpretability.

---


## Why visual grounding?

Traditional RAG systems return text snippets or page numbers, which still require manual verification.

This project explores an alternative: grounding answers directly in the source document layout by returning cropped page images alongside extracted text. This allows users to visually verify where an answer comes from, even in long, unstructured PDFs.


### **Primary AWS Skills Demonstrated**
- ✅ **AWS Bedrock** - LLM orchestration, Knowledge Bases, RAG implementation
- ✅ **Serverless Architecture** - Lambda functions with API Gateway integration
- ✅ **Container Orchestration** - ECR management for Lambda deployments
- ✅ **Infrastructure Automation** - Bash scripts for one-command deployment
- ✅ **Cloud Security** - IAM roles, environment management, audit logging
- ✅ **Observability** - CloudWatch logging, metrics, and debugging

### **Business Use Case**
Canadian government budget document analysis system enabling:
- Natural language queries over PDF documents
- Semantic search with citation tracking
- Visual grounding (exact page/location references)
- Conversation memory for multi-turn interactions

---

## 🚀 Quick Demo (No Deployment Required)

**Want to see the system in action without deploying to AWS?**

👉 **Check out [`rag_end_to_end.ipynb`](./rag_end_to_end.ipynb)** - A comprehensive Jupyter notebook demonstrating:

- ✅ Complete RAG workflow from document upload to query responses
- ✅ Real examples of natural language queries and AI-generated answers
- ✅ Visual grounding with PDF citations and bounding boxes
- ✅ Conversation memory in action 

---

## 🏗️ AWS Architecture

```
                                    ┌─────────────────────────────────────┐
                                    │         AWS Cloud Services          │
                                    │                                     │
┌─────────┐                        │  ┌────────────┐   ┌──────────────┐ │
│         │                        │  │  API       │   │   Lambda     │ │
│  Client │──────HTTPS────────────▶│  │  Gateway   │──▶│  Function    │ │
│         │                        │  │  (HTTP)    │   │  (Docker)    │ │
└─────────┘                        │  └────────────┘   └──────┬───────┘ │
                                    │                           │         │
                                    │                           ▼         │
                                    │               ┌─────────────────┐  │
                                    │               │  AWS Bedrock    │  │
                                    │               │                 │  │
                                    │               │  ┌────────────┐ │  │
                                    │               │  │ Claude     │ │  │
                                    │               │  │ Opus 4.5   │ │  │
                                    │               │  └────────────┘ │  │
                                    │               │                 │  │
                                    │               │  ┌────────────┐ │  │
                                    │               │  │ Knowledge  │ │  │
                                    │               │  │ Base (RAG) │ │  │
                                    │               │  └──────┬─────┘ │  │
                                    │               │         │       │  │
                                    │               │  ┌──────▼────┐  │  │
                                    │               │  │OpenSearch │  │  │
                                    │               │  │Serverless │  │  │
                                    │               │  └───────────┘  │  │
                                    │               └─────────┬───────┘  │
                                    │                         │          │
                                    │                         ▼          │
                                    │               ┌──────────────────┐ │
                                    │               │   Amazon S3      │ │
                                    │               │  • Budget PDFs   │ │
                                    │               │  • Parsed Chunks │ │
                                    │               │  • Metadata      │ │
                                    │               └──────────────────┘ │
                                    │                                     │
                                    │  ┌────────────┐   ┌──────────────┐ │
                                    │  │ Amazon ECR │   │  CloudWatch  │ │
                                    │  │ (Images)   │   │  (Logs)      │ │
                                    │  └────────────┘   └──────────────┘ │
                                    └─────────────────────────────────────┘
```

---

## 💡 AWS Bedrock Implementation Details

### **1. Knowledge Base Configuration**
- **Vector embeddings**: Titan Embeddings G1
- **Search strategy**: Hybrid (semantic + keyword)
- **Number of results**: Top 5 with confidence scores
- **Data source**: S3 bucket with automatic syncing
- **Metadata filtering**: Document type, date, section

### **2. Claude Opus Integration**
- **Model**: `global.anthropic.claude-opus-4-5-20251101-v1:0`
- **Token limits**: 200K context window
- **Temperature**: 0.7 for balanced creativity
- **System prompt**: Custom instructions for budget analysis
- **Tool use**: Search tool integration via Strands framework

### **3. Memory Management** (Bedrock Agent Core)
- **Session summaries**: Automatic conversation summarization
- **User preferences**: Learning from interaction patterns
- **Namespaces**: Organized by actor ID and session ID

---


## 📦 Technology Stack

### **Core AWS Services**
```
AWS Bedrock (Claude Opus 4.5)
├── Knowledge Base
├── OpenSearch Serverless
└── Agent Runtime

AWS Lambda (Python 3.10)
├── Docker Container
├── 1GB Memory
└── 300s Timeout

API Gateway (HTTP API)
├── CORS Configuration
└── Lambda Integration

Supporting Services
├── Amazon S3 (Document Storage)
├── Amazon ECR (Container Registry)
├── CloudWatch (Logging & Metrics)
└── IAM (Access Control)
```

### **Python Dependencies**
- `boto3` - AWS SDK
- `bedrock-agentcore` - Memory management
- `strands-agents` - Tool framework
- `pymupdf` - PDF processing
- `landingai-ade` - visual grounding
- `pytest` - Testing framework

---


### Everything Else
In progress ... (check back later)
