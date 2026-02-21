# 🔧 REFACTORING ROADMAP: Merapihkan Arsitektur Existing

**Tanggal:** 2025-01-XX  
**Tujuan:** Align existing code dengan arsitektur definitif tanpa break functionality  
**Prinsip:** Incremental, Tested, Backward Compatible

---

## 📊 AUDIT EXISTING COMPONENTS

### ✅ Yang Sudah Benar & Berfungsi (KEEP AS IS)
```
src/local_inference/
├── rag_pipeline.py          ✅ Core RAG logic
├── inference_engine.py      ✅ LLM inference
├── complete_pipeline.py     ✅ Pipeline orchestration
└── model_manager.py         ✅ Model loading

src/embeddings/
├── chroma_manager.py        ✅ Vector DB operations
├── bedrock_client.py        ✅ AWS Bedrock integration
└── local_embeddings_client.py ✅ Local embedding option

src/data_processing/
├── etl_pipeline.py          ✅ ETL logic
├── pdf_extractor.py         ✅ PDF processing
└── text_chunker.py          ✅ Text chunking

frontend/
├── pages/                   ✅ HTML pages
├── css/                     ✅ Stylesheets
└── js/                      ✅ JavaScript logic

api_server.py                ✅ FastAPI backend (working)
```

### ⚠️ Yang Perlu Refactoring (RENAME/REORGANIZE)
```
src/local_inference/        → src/edge_runtime/
src/cloud_sync/             → src/aws_control_plane/
models/cache/               → models/
```

### ❌ Yang Belum Ada (CREATE NEW)
```
src/persistence/            → Database layer (PostgreSQL)
src/pedagogy/               → Pedagogical engine
src/resilience/             → Backup & recovery
src/telemetry/              → Aggregated metrics (expand)
database/                   → SQL schemas
aws_lambda/                 → Lambda functions
infrastructure/             → AWS setup scripts
```

---

## 🎯 REFACTORING STRATEGY

### Prinsip Utama:
1. **Incremental** - Satu modul per waktu
2. **Tested** - Test sebelum & sesudah refactor
3. **Backward Compatible** - Jangan break existing functionality
4. **Git Branching** - Setiap fase di branch terpisah

---

## 📋 FASE-FASE REFACTORING


### **FASE 0: PREPARATION (Hari 1-2)**

#### Step 0.1: Backup Everything
```bash
# Create backup branch
git checkout -b backup-before-refactor
git add .
git commit -m "Backup: Before architecture refactoring"
git push origin backup-before-refactor

# Create working branch
git checkout -b refactor-architecture-alignment
```

#### Step 0.2: Document Current State
```bash
# Test semua yang ada sekarang
python scripts/check_system_ready.py > audit/current_state.txt
pytest tests/ > audit/test_results_before.txt

# List semua file
find src/ -type f -name "*.py" > audit/file_inventory.txt
```

#### Step 0.3: Create Refactoring Checklist
```bash
# Copy template ini ke file tracking
cp REFACTORING_ROADMAP.md REFACTORING_PROGRESS.md

# Track progress di REFACTORING_PROGRESS.md
```

---

### **FASE 1: FOLDER RESTRUCTURING (Hari 3-5)**

#### Step 1.1: Rename Core Folders (Safe Rename)
```bash
# Rename dengan Git (preserve history)
git mv src/local_inference src/edge_runtime
git mv src/cloud_sync src/aws_control_plane

# Update imports di semua file
# Gunakan find & replace:
# "from src.local_inference" → "from src.edge_runtime"
# "from src.cloud_sync" → "from src.aws_control_plane"
```

#### Step 1.2: Fix Model Path
```bash
# Pindahkan models dari cache ke root
mv models/cache/*.gguf models/ 2>/dev/null || true
rmdir models/cache 2>/dev/null || true

# Update config
# Edit config/app_config.py:
# self.local_model_path = './models/openclass-nexus-q4.gguf'
# (bukan './models/cache/...')
```

#### Step 1.3: Create New Folder Structure
```bash
# Buat folder baru yang dibutuhkan
mkdir -p src/persistence
mkdir -p src/pedagogy
mkdir -p src/resilience
mkdir -p database
mkdir -p aws_lambda
mkdir -p infrastructure

# Buat __init__.py
touch src/persistence/__init__.py
touch src/pedagogy/__init__.py
touch src/resilience/__init__.py
```

#### Step 1.4: Test After Rename
```bash
# Test import masih jalan
python -c "from src.edge_runtime.rag_pipeline import RAGPipeline; print('OK')"
python -c "from src.aws_control_plane.s3_storage_manager import S3StorageManager; print('OK')"

# Run existing tests
pytest tests/ -v
```

**Commit Point:**
```bash
git add .
git commit -m "refactor: Rename folders to match definitive architecture"
```

---

### **FASE 2: DATABASE PERSISTENCE LAYER (Hari 6-10)**

#### Step 2.1: Setup PostgreSQL
```bash
# Install PostgreSQL (jika belum)
# Ubuntu/Debian:
sudo apt install postgresql postgresql-contrib

# Windows: Download installer
# https://www.postgresql.org/download/windows/

# Create database
sudo -u postgres psql -c "CREATE DATABASE nexusai_school;"
sudo -u postgres psql -c "CREATE USER nexusai WITH PASSWORD 'nexusai2025';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE nexusai_school TO nexusai;"
```

#### Step 2.2: Create Database Schema
```bash
# Buat file schema
cat > database/schema.sql << 'EOF'
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('siswa', 'guru', 'admin')),
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subjects table (Dynamic subjects)
CREATE TABLE subjects (
    id SERIAL PRIMARY KEY,
    grade INTEGER NOT NULL CHECK (grade BETWEEN 10 AND 12),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Books table (Dynamic curriculum)
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    filename VARCHAR(255),
    vkp_version VARCHAR(20),
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat history table
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table (Token management)
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_chat_history_user ON chat_history(user_id);
CREATE INDEX idx_chat_history_created ON chat_history(created_at);
CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
EOF

# Apply schema
psql -U nexusai -d nexusai_school -f database/schema.sql
```

#### Step 2.3: Create ORM Models
```bash
# Install dependencies
pip install sqlalchemy psycopg2-binary

# Buat models
cat > src/persistence/models.py << 'EOF'
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    full_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")

class Subject(Base):
    __tablename__ = 'subjects'
    id = Column(Integer, primary_key=True)
    grade = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    books = relationship("Book", back_populates="subject", cascade="all, delete-orphan")

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey('subjects.id'))
    title = Column(String(255), nullable=False)
    filename = Column(String(255))
    vkp_version = Column(String(20))
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    subject = relationship("Subject", back_populates="books")

class ChatHistory(Base):
    __tablename__ = 'chat_history'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    subject_id = Column(Integer, ForeignKey('subjects.id'))
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="chat_history")

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="sessions")

# Database connection
DATABASE_URL = "postgresql://nexusai:nexusai2025@localhost/nexusai_school"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOF
```

#### Step 2.4: Create Database Manager
```bash
cat > src/persistence/db_manager.py << 'EOF'
from .models import User, Subject, Book, ChatHistory, Session, get_db
from sqlalchemy.orm import Session as DBSession
from datetime import datetime, timedelta
import hashlib

class DatabaseManager:
    def __init__(self):
        pass
    
    # User operations
    def create_user(self, username: str, password: str, role: str, full_name: str = None):
        db = next(get_db())
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user = User(username=username, password_hash=password_hash, role=role, full_name=full_name)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def get_user_by_username(self, username: str):
        db = next(get_db())
        return db.query(User).filter(User.username == username).first()
    
    # Session operations
    def create_session(self, user_id: int, token: str, expires_hours: int = 24):
        db = next(get_db())
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        session = Session(user_id=user_id, token=token, expires_at=expires_at)
        db.add(session)
        db.commit()
        return session
    
    def get_session_by_token(self, token: str):
        db = next(get_db())
        return db.query(Session).filter(Session.token == token).first()
    
    # Chat history operations
    def save_chat(self, user_id: int, subject_id: int, question: str, response: str, confidence: float = None):
        db = next(get_db())
        chat = ChatHistory(
            user_id=user_id,
            subject_id=subject_id,
            question=question,
            response=response,
            confidence=confidence
        )
        db.add(chat)
        db.commit()
        return chat
    
    # Subject operations
    def create_subject(self, grade: int, name: str, code: str):
        db = next(get_db())
        subject = Subject(grade=grade, name=name, code=code)
        db.add(subject)
        db.commit()
        db.refresh(subject)
        return subject
    
    def get_all_subjects(self):
        db = next(get_db())
        return db.query(Subject).all()
EOF
```

#### Step 2.5: Migrate api_server.py to Use Database
```bash
# Backup current api_server.py
cp api_server.py api_server.py.backup

# Update api_server.py:
# 1. Import DatabaseManager
# 2. Replace in-memory dicts dengan database calls
# 3. Test authentication dengan database
# 4. Test chat history persistence

# Detailed migration akan di-handle per function
```

**Commit Point:**
```bash
git add .
git commit -m "feat: Add PostgreSQL persistence layer"
```

---

### **FASE 3: AWS INFRASTRUCTURE SETUP (Hari 11-15)**

#### Step 3.1: Create AWS Setup Scripts
```bash
mkdir -p infrastructure/terraform
mkdir -p infrastructure/scripts

# Buat setup script
cat > infrastructure/scripts/setup_aws.sh << 'EOF'
#!/bin/bash
# AWS Infrastructure Setup Script

echo "Setting up AWS infrastructure for NexusAI..."

# Create S3 buckets
aws s3 mb s3://nexusai-curriculum-raw --region ap-southeast-1
aws s3 mb s3://nexusai-vkp-packages --region ap-southeast-1
aws s3 mb s3://nexusai-model-distribution --region ap-southeast-1

# Enable versioning on VKP bucket
aws s3api put-bucket-versioning \
    --bucket nexusai-vkp-packages \
    --versioning-configuration Status=Enabled

# Create DynamoDB tables
aws dynamodb create-table \
    --table-name nexusai-schools \
    --attribute-definitions AttributeName=school_id,AttributeType=S \
    --key-schema AttributeName=school_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region ap-southeast-1

aws dynamodb create-table \
    --table-name nexusai-metrics \
    --attribute-definitions AttributeName=school_id,AttributeType=S AttributeName=timestamp,AttributeType=N \
    --key-schema AttributeName=school_id,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region ap-southeast-1

echo "AWS infrastructure setup complete!"
EOF

chmod +x infrastructure/scripts/setup_aws.sh
```

#### Step 3.2: Create Lambda Function for Curriculum Processing
```bash
mkdir -p aws_lambda/curriculum_processor

cat > aws_lambda/curriculum_processor/lambda_function.py << 'EOF'
import json
import boto3
import os
from pypdf import PdfReader
from io import BytesIO

s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

def lambda_handler(event, context):
    # Get S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    print(f"Processing: s3://{bucket}/{key}")
    
    # Download PDF
    pdf_obj = s3.get_object(Bucket=bucket, Key=key)
    pdf_content = pdf_obj['Body'].read()
    
    # Extract text
    pdf_reader = PdfReader(BytesIO(pdf_content))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    
    # Chunk text (simplified)
    chunks = chunk_text(text, chunk_size=800, overlap=100)
    
    # Generate embeddings
    embeddings = []
    for chunk in chunks:
        embedding = generate_embedding(chunk)
        embeddings.append({
            'text': chunk,
            'embedding': embedding
        })
    
    # Package VKP
    vkp_data = {
        'version': '1.0.0',
        'source_file': key,
        'chunks': len(chunks),
        'embeddings': embeddings
    }
    
    # Upload VKP to S3
    vkp_key = key.replace('raw/', 'vkp/').replace('.pdf', '.json')
    s3.put_object(
        Bucket='nexusai-vkp-packages',
        Key=vkp_key,
        Body=json.dumps(vkp_data)
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Processed: {key}')
    }

def chunk_text(text, chunk_size=800, overlap=100):
    # Simplified chunking
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def generate_embedding(text):
    # Call Bedrock Titan
    response = bedrock.invoke_model(
        modelId='amazon.titan-embed-text-v1',
        body=json.dumps({'inputText': text})
    )
    result = json.loads(response['body'].read())
    return result['embedding']
EOF

# Create requirements.txt for Lambda
cat > aws_lambda/curriculum_processor/requirements.txt << 'EOF'
boto3
pypdf
EOF
```

#### Step 3.3: Deploy Lambda Function
```bash
# Package Lambda
cd aws_lambda/curriculum_processor
pip install -r requirements.txt -t .
zip -r function.zip .

# Deploy
aws lambda create-function \
    --function-name nexusai-curriculum-processor \
    --runtime python3.11 \
    --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://function.zip \
    --timeout 300 \
    --memory-size 1024

# Add S3 trigger
aws lambda add-permission \
    --function-name nexusai-curriculum-processor \
    --statement-id s3-trigger \
    --action lambda:InvokeFunction \
    --principal s3.amazonaws.com \
    --source-arn arn:aws:s3:::nexusai-curriculum-raw

cd ../..
```

**Commit Point:**
```bash
git add .
git commit -m "feat: Add AWS infrastructure and Lambda processor"
```

---

### **FASE 4: VKP PULL MECHANISM (Hari 16-18)**

#### Step 4.1: Create VKP Puller
```bash
cat > src/aws_control_plane/vkp_puller.py << 'EOF'
import boto3
import json
from pathlib import Path
from src.embeddings.chroma_manager import ChromaDBManager
from src.persistence.db_manager import DatabaseManager

class VKPPuller:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.bucket = 'nexusai-vkp-packages'
        self.chroma = ChromaDBManager()
        self.db = DatabaseManager()
    
    def check_updates(self):
        # List VKP files in S3
        response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix='vkp/')
        
        for obj in response.get('Contents', []):
            key = obj['Key']
            version = self.extract_version(key)
            
            # Check if we have this version locally
            if not self.is_version_installed(version):
                print(f"New version found: {version}")
                self.download_and_install(key, version)
    
    def download_and_install(self, key, version):
        # Download VKP
        vkp_obj = self.s3.get_object(Bucket=self.bucket, Key=key)
        vkp_data = json.loads(vkp_obj['Body'].read())
        
        # Extract embeddings
        for item in vkp_data['embeddings']:
            self.chroma.add_document(
                text=item['text'],
                embedding=item['embedding'],
                metadata={'version': version}
            )
        
        print(f"Installed version: {version}")
    
    def extract_version(self, key):
        # Extract version from key
        return key.split('/')[-1].replace('.json', '')
    
    def is_version_installed(self, version):
        # Check database for installed versions
        # Simplified check
        return False

if __name__ == '__main__':
    puller = VKPPuller()
    puller.check_updates()
EOF
```

#### Step 4.2: Setup Cron Job
```bash
# Linux crontab
cat > infrastructure/scripts/setup_cron.sh << 'EOF'
#!/bin/bash
# Add cron job for VKP puller

(crontab -l 2>/dev/null; echo "0 * * * * /usr/bin/python3 /path/to/src/aws_control_plane/vkp_puller.py") | crontab -

echo "Cron job added: VKP puller runs every hour"
EOF

chmod +x infrastructure/scripts/setup_cron.sh
```

**Commit Point:**
```bash
git add .
git commit -m "feat: Add VKP pull mechanism with cron"
```

---

## 🎯 NEXT STEPS SUMMARY

### Immediate Actions (This Week):
1. ✅ Run FASE 0: Backup & preparation
2. ✅ Run FASE 1: Folder restructuring
3. ⏭️ Test everything still works after rename

### Short-term (Next 2 Weeks):
4. ⏭️ Run FASE 2: Database persistence
5. ⏭️ Migrate api_server.py to use PostgreSQL
6. ⏭️ Test persistence (restart server, data tetap ada)

### Mid-term (Next Month):
7. ⏭️ Run FASE 3: AWS infrastructure
8. ⏭️ Run FASE 4: VKP pull mechanism
9. ⏭️ Test end-to-end: Upload PDF → AWS → School Server

### Long-term (Next 2-3 Months):
10. ⏭️ Implement Pedagogical Engine (FASE 4 dari DEVELOPMENT_STRATEGY.md)
11. ⏭️ Implement Resilience (FASE 5)
12. ⏭️ Load testing & optimization (FASE 6)

---

## 📝 TRACKING PROGRESS

Create file: `REFACTORING_PROGRESS.md`
```markdown
# Refactoring Progress Tracker

## FASE 0: PREPARATION
- [ ] Step 0.1: Backup everything
- [ ] Step 0.2: Document current state
- [ ] Step 0.3: Create checklist

## FASE 1: FOLDER RESTRUCTURING
- [ ] Step 1.1: Rename core folders
- [ ] Step 1.2: Fix model path
- [ ] Step 1.3: Create new folders
- [ ] Step 1.4: Test after rename

## FASE 2: DATABASE PERSISTENCE
- [ ] Step 2.1: Setup PostgreSQL
- [ ] Step 2.2: Create schema
- [ ] Step 2.3: Create ORM models
- [ ] Step 2.4: Create DB manager
- [ ] Step 2.5: Migrate api_server.py

## FASE 3: AWS INFRASTRUCTURE
- [ ] Step 3.1: Create setup scripts
- [ ] Step 3.2: Create Lambda function
- [ ] Step 3.3: Deploy Lambda

## FASE 4: VKP PULL MECHANISM
- [ ] Step 4.1: Create VKP puller
- [ ] Step 4.2: Setup cron job

---
Last Updated: [DATE]
Current Phase: FASE 0
```

---

**PENTING:**
- Jangan skip testing di setiap fase
- Commit setelah setiap fase selesai
- Jika ada error, rollback ke commit sebelumnya
- Update REFACTORING_PROGRESS.md setiap hari

**Status:** REFACTORING ROADMAP READY  
**Next Action:** Run FASE 0 - Backup & Preparation
