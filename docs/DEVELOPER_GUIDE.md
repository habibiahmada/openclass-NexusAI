# OpenClass Nexus AI - Developer Guide

## 🛠️ Environment Setup

### Prerequisites
- **Python 3.10+**
- **Git**
- **AWS Account** (for cloud features)
- **4GB+ RAM** (8GB recommended)

### 1. Installation
```bash
# Clone repository
git clone https://github.com/habibiahmada/openclass-NexusAI.git
cd openclass-nexus

# Create virtual environment
python -m venv openclass-env
source openclass-env/bin/activate  # Linux/Mac
# or
openclass-env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Copy `.env.example` to `.env` and configure your AWS credentials:
```env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_NAME=openclass-nexus-data-unique-id
```

### 3. AWS Setup (Optional for Local-Only)
```bash
python scripts/setup_aws.py
python scripts/test_aws_connection.py
```

---

## 📂 Project Structure

```
openclass-nexus/
├── src/                    # Source code
│   ├── data_processing/    # ETL pipeline
│   ├── embeddings/         # Vector DB operations
│   ├── local_inference/    # AI engine (llama.cpp)
│   ├── ui/                 # Streamlit interface
│   └── cloud_sync/         # AWS synchronization
├── config/                 # Configuration files
├── data/                   # Data storage (local)
├── docs/                   # Documentation
├── models/                 # AI models (GGUF)
├── scripts/                # Utility scripts
└── tests/                  # Test suite
```

## 🧪 Development Workflow

### Running Tests
```bash
pytest tests/
```

### Code Style
- Follow PEP 8
- Use `black` and `flake8` for formatting

### Git Workflow
1. Fork & Clone
2. Create Feature Branch (`git checkout -b feature/name`)
3. Commit & Push
4. Open Pull Request
