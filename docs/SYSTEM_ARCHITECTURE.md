# OpenClass Nexus AI - System Architecture

## 🏗️ High-Level Architecture

The system is designed to operate in two modes: **Cloud-Connected Maintenance** and **Offline Inference**.

```mermaid
graph TB
    subgraph "Local School Environment (Offline)"
        UI[Streamlit UI]
        RAG[RAG Pipeline]
        LLM[Llama-3.2-3B (GGUF)]
        VDB[ChromaDB]
    end
    
    subgraph "Cloud Infrastructure (Maintenance)"
        AWS[AWS S3 & Bedrock]
        Updates[Content Updates]
    end
    
    UI --> RAG
    RAG --> VDB
    RAG --> LLM
    AWS -.->|Sync| VDB
```

## 🧩 Core Components

### 1. Local Inference Engine
- **Model**: Llama-3.2-3B-Instruct (Quantized to GGUF Q4_K_M)
- **Runtime**: `llama.cpp` python bindings
- ** Constraints**: Optimized for <4GB RAM utilization

### 2. RAG Pipeline
- **Vector DB**: ChromaDB (locally hosted)
- **Embeddings**: AWS Bedrock Titan (cached locally)
- **Context**: 4096 token window

### 3. Data Processing (ETL)
- **Input**: PDF Textbooks (BSE Kemdikbud)
- **Process**: Extraction -> Chunking -> Embedding -> Indexing
- **Output**: Structured Vector Database

## 🛠️ Technology Stack

| Component | Technology | Role |
|-----------|------------|------|
| **Language** | Python 3.10+ | Core logic |
| **Interface** | Streamlit | User UI |
| **AI Model** | Llama 3.2 | Text Generation |
| **Vector DB** | ChromaDB | Semantic Search |
| **Cloud** | AWS S3, Bedrock | Storage & Embeddings |
| **Infra** | AWS CloudFront | Content Delivery |

## 📊 Performance Targets
- **Response Time**: < 5 seconds on 4GB RAM
- **Offline Capability**: 100% functional without internet
- **Accuracy**: > 85% curriculum alignment
