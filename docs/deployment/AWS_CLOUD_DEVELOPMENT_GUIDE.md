# 🚀 Panduan Lengkap: Development OpenClass Nexus AI di AWS Cloud

**Tujuan:** Setup environment development di AWS untuk mengurangi beban laptop lokal

**Target Audience:** Developer yang ingin mengembangkan proyek di cloud

**Estimasi Waktu Setup:** 2-3 jam

**Estimasi Biaya:** $100-200/bulan (development environment)

---

## 📋 Daftar Isi

1. [Prasyarat](#prasyarat)
2. [Arsitektur Development di AWS](#arsitektur-development-di-aws)
3. [Tahap 1: Setup AWS Account & IAM](#tahap-1-setup-aws-account--iam)
4. [Tahap 2: Launch EC2 Instance](#tahap-2-launch-ec2-instance)
5. [Tahap 3: Setup Database & Cache](#tahap-3-setup-database--cache)
6. [Tahap 4: Install Dependencies](#tahap-4-install-dependencies)
7. [Tahap 5: Deploy Aplikasi](#tahap-5-deploy-aplikasi)
8. [Tahap 6: Setup S3 & CloudFront](#tahap-6-setup-s3--cloudfront)
9. [Tahap 7: Monitoring & Backup](#tahap-7-monitoring--backup)
10. [Tahap 8: Remote Development Setup](#tahap-8-remote-development-setup)
11. [Troubleshooting](#troubleshooting)
12. [Cost Optimization](#cost-optimization)

---

## Prasyarat

### Yang Anda Butuhkan:

1. **AWS Account**
   - Akun AWS aktif (free tier atau paid)
   - Credit card untuk verifikasi
   - Email aktif

2. **Local Tools**
   - Git
   - SSH client (PuTTY untuk Windows atau terminal untuk Linux/Mac)
   - VS Code (optional, untuk remote development)

3. **Pengetahuan Dasar**
   - Basic Linux command line
   - Basic AWS console navigation
   - Git basics


---

## Arsitektur Development di AWS

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR LAPTOP                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  VS Code Remote SSH                              │  │
│  │  Git Client                                      │  │
│  │  Browser (untuk akses web UI)                    │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ SSH / HTTPS
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    AWS CLOUD                            │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │         EC2 Instance (t3.xlarge)                │  │
│  │  ┌──────────────────────────────────────────┐  │  │
│  │  │ Ubuntu 22.04 LTS                         │  │  │
│  │  │ - Python 3.10                            │  │  │
│  │  │ - OpenClass Nexus AI Code                │  │  │
│  │  │ - LLM Runtime (Llama 3.2-3B)             │  │  │
│  │  │ - ChromaDB Vector Database               │  │  │
│  │  │ - FastAPI Server                         │  │  │
│  │  └──────────────────────────────────────────┘  │  │
│  │  Storage: 200GB EBS SSD                         │  │
│  │  RAM: 16GB                                      │  │
│  │  vCPU: 4 cores                                  │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │         RDS PostgreSQL (Optional)               │  │
│  │  - db.t3.micro (20GB storage)                   │  │
│  │  - Untuk production-ready persistence          │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │         ElastiCache Redis (Optional)            │  │
│  │  - cache.t3.micro                               │  │
│  │  - Untuk caching layer                          │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │         S3 Buckets                              │  │
│  │  - nexusai-curriculum-raw                       │  │
│  │  - nexusai-vkp-packages                         │  │
│  │  - nexusai-model-distribution                   │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │         CloudFront CDN                          │  │
│  │  - Distribusi model & konten                    │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Komponen Utama:

1. **EC2 Instance**: Server utama untuk development
2. **RDS PostgreSQL**: Database (optional, bisa pakai PostgreSQL di EC2)
3. **ElastiCache Redis**: Cache layer (optional, bisa pakai Redis di EC2)
4. **S3**: Storage untuk model, dataset, backup
5. **CloudFront**: CDN untuk distribusi konten
6. **Security Groups**: Firewall untuk akses


---

## Tahap 1: Setup AWS Account & IAM

### 1.1 Buat AWS Account (Jika Belum Punya)

1. Kunjungi: https://aws.amazon.com/
2. Klik "Create an AWS Account"
3. Isi informasi:
   - Email address
   - Password
   - AWS account name
4. Pilih account type: "Personal"
5. Isi informasi pembayaran (credit card)
6. Verifikasi identitas (phone verification)
7. Pilih support plan: "Basic Support - Free"

### 1.2 Setup IAM User untuk Development

**Mengapa IAM User?** Jangan gunakan root account untuk development (security best practice)

**Langkah-langkah:**

1. Login ke AWS Console: https://console.aws.amazon.com/
2. Cari service "IAM" di search bar
3. Klik "Users" di sidebar kiri
4. Klik "Add users"
5. Isi detail:
   - User name: `openclass-dev`
   - Access type: ✅ Programmatic access, ✅ AWS Management Console access
   - Console password: Custom password atau Auto-generated
   - ✅ Require password reset (optional)
6. Klik "Next: Permissions"
7. Pilih "Attach existing policies directly"
8. Cari dan centang policies berikut:
   - `AmazonEC2FullAccess`
   - `AmazonS3FullAccess`
   - `AmazonRDSFullAccess`
   - `AmazonElastiCacheFullAccess`
   - `CloudFrontFullAccess`
   - `IAMReadOnlyAccess`
9. Klik "Next: Tags" (skip)
10. Klik "Next: Review"
11. Klik "Create user"
12. **PENTING:** Download credentials CSV atau copy:
    - Access key ID
    - Secret access key
    - Console login link

### 1.3 Setup AWS CLI di Laptop (Optional)

```bash
# Install AWS CLI
# Windows (PowerShell)
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Mac
brew install awscli

# Configure AWS CLI
aws configure
# AWS Access Key ID: [paste dari step 1.2]
# AWS Secret Access Key: [paste dari step 1.2]
# Default region name: ap-southeast-2
# Default output format: json
```


---

## Tahap 2: Launch EC2 Instance

### 2.1 Pilih Region

1. Di AWS Console, pilih region terdekat di kanan atas
2. Rekomendasi untuk Indonesia:
   - **Singapore (ap-southeast-1)** - Paling dekat, latency rendah
   - **Sydney (ap-southeast-2)** - Alternatif, support Bedrock
   - **Tokyo (ap-northeast-1)** - Alternatif

### 2.2 Launch EC2 Instance

1. Cari service "EC2" di search bar
2. Klik "Launch Instance"
3. **Name and tags:**
   - Name: `openclass-dev-server`
   - Tags (optional): `Environment: Development`, `Project: OpenClass`

4. **Application and OS Images (AMI):**
   - Quick Start: Ubuntu
   - AMI: **Ubuntu Server 22.04 LTS (HVM), SSD Volume Type**
   - Architecture: 64-bit (x86)

5. **Instance type:**
   - Pilih: **t3.xlarge**
     - vCPU: 4
     - Memory: 16 GiB
     - Network Performance: Up to 5 Gigabit
   - Biaya: ~$0.1664/hour (~$120/bulan jika running 24/7)
   
   **Alternatif lebih murah (untuk testing):**
   - **t3.large** (2 vCPU, 8GB RAM) - $60/bulan
   - **t3.medium** (2 vCPU, 4GB RAM) - $30/bulan (minimal, mungkin lambat)

6. **Key pair (login):**
   - Klik "Create new key pair"
   - Key pair name: `openclass-dev-key`
   - Key pair type: RSA
   - Private key file format: 
     - `.pem` untuk Linux/Mac
     - `.ppk` untuk Windows (PuTTY)
   - Klik "Create key pair"
   - **PENTING:** File akan otomatis download, simpan di tempat aman!

7. **Network settings:**
   - Klik "Edit"
   - VPC: Default VPC (atau buat baru jika perlu)
   - Subnet: No preference
   - Auto-assign public IP: **Enable**
   - Firewall (security groups): **Create security group**
     - Security group name: `openclass-dev-sg`
     - Description: `Security group for OpenClass development server`
     - Inbound rules:
       - Rule 1: SSH
         - Type: SSH
         - Protocol: TCP
         - Port: 22
         - Source: My IP (akan otomatis detect IP Anda)
       - Rule 2: Custom TCP (untuk FastAPI)
         - Type: Custom TCP
         - Protocol: TCP
         - Port: 8000
         - Source: My IP
       - Rule 3: HTTP (optional, untuk web access)
         - Type: HTTP
         - Protocol: TCP
         - Port: 80
         - Source: Anywhere (0.0.0.0/0)
       - Rule 4: HTTPS (optional)
         - Type: HTTPS
         - Protocol: TCP
         - Port: 443
         - Source: Anywhere (0.0.0.0/0)

8. **Configure storage:**
   - Root volume:
     - Size: **200 GiB** (untuk model, vector DB, dataset)
     - Volume type: **gp3** (General Purpose SSD)
     - IOPS: 3000 (default)
     - Throughput: 125 MB/s (default)
     - Delete on termination: ✅ (atau uncheck jika ingin keep data)
     - Encrypted: ✅ (recommended)

9. **Advanced details (optional):**
   - Monitoring: Enable CloudWatch detailed monitoring (optional, +$2/bulan)
   - Termination protection: Enable (recommended, prevent accidental deletion)

10. **Summary:**
    - Review semua konfigurasi
    - Estimated cost: ~$120-150/bulan

11. Klik **"Launch instance"**

12. Tunggu 2-3 menit hingga instance status: **Running**

### 2.3 Allocate Elastic IP (Optional tapi Recommended)

**Mengapa?** Agar IP publik tidak berubah setiap kali instance restart

1. Di EC2 Dashboard, klik "Elastic IPs" di sidebar
2. Klik "Allocate Elastic IP address"
3. Network Border Group: Default
4. Klik "Allocate"
5. Pilih Elastic IP yang baru dibuat
6. Klik "Actions" → "Associate Elastic IP address"
7. Instance: Pilih `openclass-dev-server`
8. Private IP: Pilih IP yang muncul
9. Klik "Associate"

**Note:** Elastic IP gratis selama attached ke running instance, tapi dikenakan biaya jika tidak digunakan


---

## Tahap 3: Setup Database & Cache

### Opsi A: Install di EC2 (Lebih Murah, Recommended untuk Development)

**Keuntungan:**
- Tidak ada biaya tambahan
- Lebih mudah setup
- Cukup untuk development

**Kekurangan:**
- Tidak managed (harus maintain sendiri)
- Backup manual

**Langkah:** Akan diinstall di Tahap 4

### Opsi B: Gunakan RDS & ElastiCache (Production-Ready)

**Keuntungan:**
- Fully managed
- Automatic backup
- High availability
- Scalable

**Kekurangan:**
- Biaya tambahan ~$30-50/bulan

#### 3.1 Setup RDS PostgreSQL (Optional)

1. Cari service "RDS" di AWS Console
2. Klik "Create database"
3. **Choose a database creation method:**
   - Standard create
4. **Engine options:**
   - Engine type: PostgreSQL
   - Version: PostgreSQL 15.x (latest stable)
5. **Templates:**
   - Dev/Test (lebih murah)
6. **Settings:**
   - DB instance identifier: `openclass-dev-db`
   - Master username: `postgres`
   - Master password: [buat password kuat, simpan di tempat aman]
   - Confirm password
7. **Instance configuration:**
   - DB instance class: Burstable classes (includes t classes)
   - db.t3.micro (1 vCPU, 1GB RAM) - Free tier eligible
8. **Storage:**
   - Storage type: General Purpose SSD (gp3)
   - Allocated storage: 20 GiB
   - ✅ Enable storage autoscaling (max 100 GiB)
9. **Connectivity:**
   - VPC: Default VPC (sama dengan EC2)
   - Subnet group: default
   - Public access: **No** (hanya bisa diakses dari EC2)
   - VPC security group: Create new
     - Name: `openclass-db-sg`
   - Availability Zone: No preference
10. **Database authentication:**
    - Password authentication
11. **Additional configuration:**
    - Initial database name: `openclass_db`
    - Backup retention: 7 days
    - ✅ Enable automatic backups
    - Backup window: No preference
    - Maintenance window: No preference
12. Klik "Create database"
13. Tunggu 5-10 menit hingga status: **Available**

#### 3.2 Setup Security Group untuk RDS

1. Klik database yang baru dibuat
2. Tab "Connectivity & security"
3. Klik security group (openclass-db-sg)
4. Tab "Inbound rules"
5. Klik "Edit inbound rules"
6. Klik "Add rule"
   - Type: PostgreSQL
   - Protocol: TCP
   - Port: 5432
   - Source: Custom → Pilih security group EC2 (`openclass-dev-sg`)
7. Klik "Save rules"

#### 3.3 Setup ElastiCache Redis (Optional)

1. Cari service "ElastiCache" di AWS Console
2. Klik "Create"
3. **Cluster engine:**
   - Redis
4. **Location:**
   - AWS Cloud
5. **Cluster settings:**
   - Cluster mode: Disabled
   - Name: `openclass-dev-cache`
   - Engine version: 7.x (latest)
6. **Cluster settings:**
   - Node type: cache.t3.micro (0.5GB memory)
   - Number of replicas: 0 (untuk development)
7. **Subnet group:**
   - Create new
   - Name: `openclass-cache-subnet`
   - VPC: Default VPC
   - Subnets: Pilih semua available
8. **Security:**
   - Security groups: Create new
     - Name: `openclass-cache-sg`
9. **Backup:**
   - Enable automatic backups: No (untuk development)
10. Klik "Create"
11. Tunggu 5-10 menit hingga status: **Available**

#### 3.4 Setup Security Group untuk ElastiCache

1. Klik cluster yang baru dibuat
2. Klik security group
3. Edit inbound rules
4. Add rule:
   - Type: Custom TCP
   - Port: 6379
   - Source: Security group EC2 (`openclass-dev-sg`)
5. Save rules


---

## Tahap 4: Install Dependencies

### 4.1 Connect ke EC2 Instance

#### Untuk Linux/Mac:

```bash
# Set permission untuk key file
chmod 400 /path/to/openclass-dev-key.pem

# SSH ke instance
ssh -i /path/to/openclass-dev-key.pem ubuntu@<EC2-PUBLIC-IP>

# Ganti <EC2-PUBLIC-IP> dengan IP publik instance Anda
# Cek di EC2 Dashboard → Instances → pilih instance → Public IPv4 address
```

#### Untuk Windows (menggunakan PuTTY):

1. Download PuTTY: https://www.putty.org/
2. Buka PuTTYgen
3. Load file `.ppk` yang sudah didownload
4. Buka PuTTY
5. Host Name: `ubuntu@<EC2-PUBLIC-IP>`
6. Port: 22
7. Connection type: SSH
8. Di sidebar: Connection → SSH → Auth → Credentials
9. Browse dan pilih file `.ppk`
10. Klik "Open"

### 4.2 Update System

```bash
# Update package list
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y

# Install essential tools
sudo apt install -y build-essential curl wget git vim htop
```

### 4.3 Install Python 3.10+

```bash
# Check Python version (Ubuntu 22.04 sudah include Python 3.10)
python3 --version

# Install pip
sudo apt install -y python3-pip python3-venv

# Install Python development headers
sudo apt install -y python3-dev
```

### 4.4 Install PostgreSQL (Jika tidak pakai RDS)

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE openclass_db;
CREATE USER openclass_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE openclass_db TO openclass_user;
\q
EOF

# Test connection
psql -h localhost -U openclass_user -d openclass_db
# Password: your_secure_password_here
# Jika berhasil, ketik \q untuk keluar
```

### 4.5 Install Redis (Jika tidak pakai ElastiCache)

```bash
# Install Redis
sudo apt install -y redis-server

# Configure Redis untuk production
sudo nano /etc/redis/redis.conf
# Ubah:
# supervised no → supervised systemd
# bind 127.0.0.1 ::1 (pastikan hanya localhost)
# maxmemory 256mb (sesuaikan dengan kebutuhan)
# maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server

# Test Redis
redis-cli ping
# Response: PONG
```

### 4.6 Install Additional System Dependencies

```bash
# Install dependencies untuk PDF processing
sudo apt install -y poppler-utils tesseract-ocr

# Install dependencies untuk llama-cpp-python
sudo apt install -y cmake libopenblas-dev

# Install dependencies untuk ChromaDB
sudo apt install -y sqlite3 libsqlite3-dev
```


---

## Tahap 5: Deploy Aplikasi

### 5.1 Clone Repository

```bash
# Buat directory untuk project
mkdir -p ~/projects
cd ~/projects

# Clone repository
git clone https://github.com/habibiahmada/openclass-nexus-ai.git
cd openclass-nexus-ai

# Atau jika private repo, gunakan SSH atau personal access token
```

### 5.2 Setup Virtual Environment

```bash
# Create virtual environment
python3 -m venv openclass-env

# Activate virtual environment
source openclass-env/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 5.3 Install Python Dependencies

```bash
# Install requirements
pip install -r requirements.txt

# Jika ada error dengan llama-cpp-python, install dengan CMAKE_ARGS
CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" pip install llama-cpp-python --force-reinstall --no-cache-dir

# Verify installation
python -c "import llama_cpp; print('llama-cpp-python installed successfully')"
```

### 5.4 Setup Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env file
nano .env
```

**Isi .env dengan konfigurasi berikut:**

```bash
# Application Configuration
SECRET_KEY=<generate dengan: python -c "import secrets; print(secrets.token_hex(32))">
DEBUG=True
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Database Configuration (jika pakai PostgreSQL di EC2)
DATABASE_URL=postgresql://openclass_user:your_secure_password_here@localhost:5432/openclass_db

# Database Configuration (jika pakai RDS)
# DATABASE_URL=postgresql://postgres:your_rds_password@<RDS-ENDPOINT>:5432/openclass_db

# Redis Configuration (jika pakai Redis di EC2)
REDIS_URL=redis://localhost:6379/0

# Redis Configuration (jika pakai ElastiCache)
# REDIS_URL=redis://<ELASTICACHE-ENDPOINT>:6379/0

# AWS Configuration
AWS_DEFAULT_REGION=ap-southeast-2
AWS_ACCESS_KEY_ID=<your-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-secret-access-key>

# S3 Buckets
S3_CURRICULUM_RAW_BUCKET=nexusai-curriculum-raw
S3_VKP_PACKAGES_BUCKET=nexusai-vkp-packages
S3_MODEL_DISTRIBUTION_BUCKET=nexusai-model-distribution

# Bedrock Configuration
BEDROCK_REGION=ap-southeast-2
BEDROCK_MODEL_ID=amazon.titan-embed-text-v2:0

# Model Configuration
MODEL_PATH=./models/llama-3.2-3b-instruct-q4_k_m.gguf
N_CTX=4096
N_THREADS=4
N_GPU_LAYERS=0
TEMPERATURE=0.7
MAX_TOKENS=512

# Vector Database
CHROMA_PERSIST_DIRECTORY=./data/vector_db
COLLECTION_NAME=kurikulum_nasional

# CORS
CORS_ORIGINS=["http://localhost:8000","http://<EC2-PUBLIC-IP>:8000"]
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5.5 Initialize Database

```bash
# Run database initialization script
python database/init_database.py

# Verify database tables created
psql -h localhost -U openclass_user -d openclass_db -c "\dt"
```

### 5.6 Download Model (Optional - untuk testing)

```bash
# Create models directory
mkdir -p models

# Download model dari Hugging Face (contoh)
# Model size: ~2GB, butuh waktu tergantung koneksi
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf -O models/llama-3.2-3b-instruct-q4_k_m.gguf

# Atau gunakan script download jika ada
# python scripts/model/download_model.py
```

**Note:** Model akan di-download otomatis saat pertama kali dijalankan jika belum ada

### 5.7 Test Run Application

```bash
# Activate virtual environment (jika belum)
source ~/projects/openclass-nexus-ai/openclass-env/bin/activate

# Run server
cd ~/projects/openclass-nexus-ai
python api_server.py

# Server akan berjalan di http://0.0.0.0:8000
# Buka browser dan akses: http://<EC2-PUBLIC-IP>:8000
```

**Jika berhasil, Anda akan melihat:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test dari laptop:**
```bash
# Buka browser
http://<EC2-PUBLIC-IP>:8000

# Atau test dengan curl
curl http://<EC2-PUBLIC-IP>:8000/api/health
```


---

## Tahap 6: Setup S3 & CloudFront

### 6.1 Create S3 Buckets

```bash
# Gunakan AWS CLI dari EC2 instance atau laptop

# Configure AWS CLI di EC2 (jika belum)
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region name: ap-southeast-2
# Default output format: json

# Create buckets
aws s3 mb s3://nexusai-curriculum-raw --region ap-southeast-2
aws s3 mb s3://nexusai-vkp-packages --region ap-southeast-2
aws s3 mb s3://nexusai-model-distribution --region ap-southeast-2

# Verify buckets created
aws s3 ls
```

### 6.2 Configure S3 Bucket Policies

**Untuk bucket model-distribution (public read):**

```bash
# Create policy file
cat > /tmp/model-distribution-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::nexusai-model-distribution/*"
    }
  ]
}
EOF

# Apply policy
aws s3api put-bucket-policy --bucket nexusai-model-distribution --policy file:///tmp/model-distribution-policy.json

# Enable public access (disable block public access)
aws s3api put-public-access-block \
  --bucket nexusai-model-distribution \
  --public-access-block-configuration \
  "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
```

### 6.3 Setup CloudFront Distribution

1. Buka AWS Console → CloudFront
2. Klik "Create distribution"
3. **Origin settings:**
   - Origin domain: Pilih `nexusai-model-distribution.s3.ap-southeast-2.amazonaws.com`
   - Name: Auto-generated
   - Origin access: Public
4. **Default cache behavior:**
   - Viewer protocol policy: Redirect HTTP to HTTPS
   - Allowed HTTP methods: GET, HEAD
   - Cache policy: CachingOptimized
5. **Settings:**
   - Price class: Use only North America and Europe (lebih murah)
   - Alternate domain name (CNAME): Kosongkan (atau isi jika punya domain)
   - SSL certificate: Default CloudFront certificate
6. Klik "Create distribution"
7. Tunggu 10-15 menit hingga status: **Deployed**
8. Copy **Distribution domain name** (contoh: `d1234567890.cloudfront.net`)

### 6.4 Update Environment Variables

```bash
# Edit .env di EC2
nano ~/projects/openclass-nexus-ai/.env

# Tambahkan:
CLOUDFRONT_DISTRIBUTION_URL=https://d1234567890.cloudfront.net
CLOUDFRONT_DISTRIBUTION_ID=E1234567890ABC
```

### 6.5 Upload Sample Data (Optional)

```bash
# Upload sample curriculum PDF
aws s3 cp data/raw_dataset/ s3://nexusai-curriculum-raw/ --recursive

# Upload model (jika sudah ada)
aws s3 cp models/llama-3.2-3b-instruct-q4_k_m.gguf s3://nexusai-model-distribution/models/

# Verify upload
aws s3 ls s3://nexusai-curriculum-raw/
aws s3 ls s3://nexusai-model-distribution/models/
```


---

## Tahap 7: Monitoring & Backup

### 7.1 Setup Systemd Service (Auto-start on Boot)

```bash
# Create systemd service file
sudo nano /etc/systemd/system/openclass.service
```

**Isi file:**

```ini
[Unit]
Description=OpenClass Nexus AI Server
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/projects/openclass-nexus-ai
Environment="PATH=/home/ubuntu/projects/openclass-nexus-ai/openclass-env/bin"
ExecStart=/home/ubuntu/projects/openclass-nexus-ai/openclass-env/bin/python api_server.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/openclass/app.log
StandardError=append:/var/log/openclass/error.log

[Install]
WantedBy=multi-user.target
```

**Enable dan start service:**

```bash
# Create log directory
sudo mkdir -p /var/log/openclass
sudo chown ubuntu:ubuntu /var/log/openclass

# Reload systemd
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable openclass

# Start service
sudo systemctl start openclass

# Check status
sudo systemctl status openclass

# View logs
sudo tail -f /var/log/openclass/app.log
```

### 7.2 Setup Backup Script

```bash
# Create backup directory
mkdir -p ~/backups

# Create backup script
nano ~/backup-openclass.sh
```

**Isi script:**

```bash
#!/bin/bash

# Configuration
BACKUP_DIR="$HOME/backups"
PROJECT_DIR="$HOME/projects/openclass-nexus-ai"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="openclass_backup_$TIMESTAMP"
S3_BACKUP_BUCKET="nexusai-backups"  # Buat bucket ini dulu

# Create backup directory
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

# Backup database
echo "Backing up database..."
pg_dump -h localhost -U openclass_user openclass_db > "$BACKUP_DIR/$BACKUP_NAME/database.sql"

# Backup vector database
echo "Backing up vector database..."
cp -r "$PROJECT_DIR/data/vector_db" "$BACKUP_DIR/$BACKUP_NAME/"

# Backup configuration
echo "Backing up configuration..."
cp "$PROJECT_DIR/.env" "$BACKUP_DIR/$BACKUP_NAME/"
cp -r "$PROJECT_DIR/config" "$BACKUP_DIR/$BACKUP_NAME/"

# Compress backup
echo "Compressing backup..."
cd "$BACKUP_DIR"
tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

# Upload to S3
echo "Uploading to S3..."
aws s3 cp "$BACKUP_NAME.tar.gz" "s3://$S3_BACKUP_BUCKET/backups/"

# Keep only last 7 days of local backups
echo "Cleaning old local backups..."
find "$BACKUP_DIR" -name "openclass_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_NAME.tar.gz"
```

**Make executable:**

```bash
chmod +x ~/backup-openclass.sh

# Test backup
~/backup-openclass.sh
```

### 7.3 Setup Cron Job for Automatic Backup

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /home/ubuntu/backup-openclass.sh >> /var/log/openclass/backup.log 2>&1

# Save and exit
```

### 7.4 Setup CloudWatch Monitoring (Optional)

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Create CloudWatch config
sudo nano /opt/aws/amazon-cloudwatch-agent/etc/config.json
```

**Isi config:**

```json
{
  "metrics": {
    "namespace": "OpenClass/Development",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          {"name": "cpu_usage_idle", "rename": "CPU_IDLE", "unit": "Percent"},
          {"name": "cpu_usage_iowait", "rename": "CPU_IOWAIT", "unit": "Percent"}
        ],
        "totalcpu": false
      },
      "disk": {
        "measurement": [
          {"name": "used_percent", "rename": "DISK_USED", "unit": "Percent"}
        ],
        "resources": ["*"]
      },
      "mem": {
        "measurement": [
          {"name": "mem_used_percent", "rename": "MEM_USED", "unit": "Percent"}
        ]
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/openclass/app.log",
            "log_group_name": "/openclass/application",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/var/log/openclass/error.log",
            "log_group_name": "/openclass/errors",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
```

**Start CloudWatch agent:**

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```


---

## Tahap 8: Remote Development Setup

### 8.1 Setup VS Code Remote SSH

**Keuntungan:**
- Edit code di laptop, run di AWS
- Integrated terminal
- Git integration
- Extension support

**Langkah-langkah:**

1. **Install VS Code** (jika belum): https://code.visualstudio.com/

2. **Install Extension "Remote - SSH":**
   - Buka VS Code
   - Klik Extensions (Ctrl+Shift+X)
   - Cari "Remote - SSH"
   - Install extension dari Microsoft

3. **Configure SSH:**
   - Tekan F1 atau Ctrl+Shift+P
   - Ketik "Remote-SSH: Open SSH Configuration File"
   - Pilih file config (biasanya `~/.ssh/config`)
   - Tambahkan:

```
Host openclass-aws
    HostName <EC2-PUBLIC-IP>
    User ubuntu
    IdentityFile /path/to/openclass-dev-key.pem
    ServerAliveInterval 60
```

4. **Connect ke Server:**
   - Tekan F1
   - Ketik "Remote-SSH: Connect to Host"
   - Pilih "openclass-aws"
   - VS Code akan membuka window baru dan connect ke EC2
   - Tunggu beberapa detik untuk setup

5. **Open Project:**
   - File → Open Folder
   - Pilih `/home/ubuntu/projects/openclass-nexus-ai`
   - Klik OK

6. **Install Python Extension di Remote:**
   - Klik Extensions
   - Install "Python" extension dari Microsoft
   - Install "Pylance" untuk IntelliSense

7. **Select Python Interpreter:**
   - Tekan F1
   - Ketik "Python: Select Interpreter"
   - Pilih `/home/ubuntu/projects/openclass-nexus-ai/openclass-env/bin/python`

### 8.2 Setup Git Configuration

```bash
# Di terminal VS Code (atau SSH)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Setup SSH key untuk GitHub (optional)
ssh-keygen -t ed25519 -C "your.email@example.com"
cat ~/.ssh/id_ed25519.pub
# Copy output dan tambahkan ke GitHub: Settings → SSH and GPG keys → New SSH key
```

### 8.3 Development Workflow

**Workflow yang Recommended:**

1. **Edit code di VS Code** (connected ke AWS via Remote SSH)
2. **Test di terminal VS Code:**
   ```bash
   # Activate venv
   source openclass-env/bin/activate
   
   # Run server
   python api_server.py
   ```
3. **Access dari browser laptop:** `http://<EC2-PUBLIC-IP>:8000`
4. **Commit changes:**
   ```bash
   git add .
   git commit -m "Your commit message"
   git push origin main
   ```

### 8.4 Port Forwarding (Optional)

**Jika ingin akses via localhost:**

```bash
# Di laptop, buka terminal baru
ssh -i /path/to/openclass-dev-key.pem -L 8000:localhost:8000 ubuntu@<EC2-PUBLIC-IP>

# Sekarang bisa akses via: http://localhost:8000
```

**Atau di VS Code:**
- Tekan F1
- Ketik "Forward a Port"
- Masukkan port: 8000
- Akses via: http://localhost:8000


---

## Troubleshooting

### Problem 1: Cannot Connect to EC2 via SSH

**Symptoms:**
```
Connection timed out
Permission denied (publickey)
```

**Solutions:**

1. **Check Security Group:**
   - EC2 Dashboard → Security Groups
   - Pastikan inbound rule SSH (port 22) allow dari IP Anda
   - Jika IP berubah, update rule dengan "My IP"

2. **Check Key Permission:**
   ```bash
   # Linux/Mac
   chmod 400 /path/to/openclass-dev-key.pem
   ```

3. **Check Instance Status:**
   - Pastikan instance status: Running
   - Pastikan status checks: 2/2 passed

4. **Try Different SSH Command:**
   ```bash
   ssh -v -i /path/to/openclass-dev-key.pem ubuntu@<EC2-PUBLIC-IP>
   # -v untuk verbose output, lihat error detail
   ```

### Problem 2: Application Won't Start

**Symptoms:**
```
ModuleNotFoundError
ImportError
Port already in use
```

**Solutions:**

1. **Check Virtual Environment:**
   ```bash
   which python
   # Should show: /home/ubuntu/projects/openclass-nexus-ai/openclass-env/bin/python
   
   # If not, activate:
   source ~/projects/openclass-nexus-ai/openclass-env/bin/activate
   ```

2. **Reinstall Dependencies:**
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

3. **Check Port:**
   ```bash
   # Check if port 8000 is in use
   sudo lsof -i :8000
   
   # Kill process if needed
   sudo kill -9 <PID>
   ```

4. **Check Logs:**
   ```bash
   sudo tail -f /var/log/openclass/error.log
   ```

### Problem 3: Database Connection Error

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server
FATAL: password authentication failed
```

**Solutions:**

1. **Check PostgreSQL Status:**
   ```bash
   sudo systemctl status postgresql
   
   # If not running:
   sudo systemctl start postgresql
   ```

2. **Check Database Exists:**
   ```bash
   sudo -u postgres psql -l
   # Should show openclass_db
   ```

3. **Check Connection String in .env:**
   ```bash
   cat .env | grep DATABASE_URL
   # Should match your database credentials
   ```

4. **Test Connection Manually:**
   ```bash
   psql -h localhost -U openclass_user -d openclass_db
   ```

### Problem 4: Out of Memory

**Symptoms:**
```
Killed
MemoryError
```

**Solutions:**

1. **Check Memory Usage:**
   ```bash
   free -h
   htop
   ```

2. **Add Swap Space:**
   ```bash
   # Create 4GB swap file
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   
   # Make permanent
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

3. **Reduce Model Size:**
   - Gunakan model quantized lebih kecil (Q4_K_M → Q3_K_M)
   - Reduce n_ctx di .env

4. **Upgrade Instance Type:**
   - Stop instance
   - Actions → Instance Settings → Change Instance Type
   - Pilih t3.xlarge atau lebih besar

### Problem 5: Slow Performance

**Solutions:**

1. **Check CPU Usage:**
   ```bash
   htop
   # Press F5 untuk tree view
   ```

2. **Optimize Model Settings:**
   ```bash
   # Edit .env
   N_THREADS=4  # Sesuaikan dengan vCPU
   N_CTX=2048   # Reduce context window
   ```

3. **Enable Redis Cache:**
   ```bash
   # Check Redis running
   redis-cli ping
   
   # Check cache hit rate
   redis-cli info stats | grep keyspace
   ```

4. **Check Disk I/O:**
   ```bash
   iostat -x 1
   # If %util high, consider upgrading to gp3 or io2
   ```

### Problem 6: Cannot Access from Browser

**Symptoms:**
```
This site can't be reached
Connection refused
```

**Solutions:**

1. **Check Security Group:**
   - Inbound rule port 8000 allow dari 0.0.0.0/0 atau My IP

2. **Check Application Running:**
   ```bash
   sudo systemctl status openclass
   curl http://localhost:8000/api/health
   ```

3. **Check Firewall:**
   ```bash
   sudo ufw status
   # If active, allow port:
   sudo ufw allow 8000
   ```

4. **Use Correct URL:**
   ```
   http://<EC2-PUBLIC-IP>:8000
   # NOT https (unless you setup SSL)
   ```


---

## Cost Optimization

### Estimasi Biaya Bulanan

#### Setup Minimal (Development):
```
EC2 t3.xlarge (16GB RAM, 4 vCPU)     : $120/bulan
EBS 200GB gp3                        : $16/bulan
Data Transfer Out (10GB)             : $1/bulan
S3 Storage (50GB)                    : $1/bulan
CloudFront (10GB transfer)           : $1/bulan
Elastic IP (attached)                : $0/bulan
─────────────────────────────────────────────
TOTAL                                : ~$139/bulan
```

#### Setup dengan RDS & ElastiCache:
```
EC2 t3.xlarge                        : $120/bulan
EBS 200GB gp3                        : $16/bulan
RDS db.t3.micro (20GB)               : $15/bulan
ElastiCache cache.t3.micro           : $12/bulan
S3 Storage (50GB)                    : $1/bulan
CloudFront (10GB transfer)           : $1/bulan
Data Transfer                        : $2/bulan
─────────────────────────────────────────────
TOTAL                                : ~$167/bulan
```

### Tips Menghemat Biaya

#### 1. Gunakan Spot Instances (Hemat 70%)

**Untuk development yang tidak 24/7:**

```bash
# Request Spot Instance saat launch
# Di EC2 Console → Launch Instance → Advanced Details
# Purchasing option: Request Spot instances
# Maximum price: $0.05/hour (adjust based on current price)

# Biaya: ~$36/bulan (vs $120 on-demand)
```

**Catatan:** Spot instance bisa di-terminate AWS kapan saja jika harga naik

#### 2. Stop Instance Saat Tidak Digunakan

```bash
# Stop instance (tidak dikenakan biaya EC2, hanya EBS)
aws ec2 stop-instances --instance-ids i-1234567890abcdef0

# Start instance saat butuh
aws ec2 start-instances --instance-ids i-1234567890abcdef0

# Hemat: ~$80/bulan jika hanya running 8 jam/hari
```

**Automation dengan Lambda:**

```python
# Lambda function untuk auto-stop jam 6 sore, auto-start jam 9 pagi
import boto3

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    
    if event['action'] == 'stop':
        ec2.stop_instances(InstanceIds=['i-1234567890abcdef0'])
    elif event['action'] == 'start':
        ec2.start_instances(InstanceIds=['i-1234567890abcdef0'])
    
    return {'statusCode': 200}

# Setup EventBridge rule:
# - Stop: cron(0 10 * * ? *)  # 6 PM WIB = 10 AM UTC
# - Start: cron(0 2 * * ? *)  # 9 AM WIB = 2 AM UTC
```

#### 3. Gunakan Reserved Instances (Hemat 40%)

**Jika yakin akan pakai 1 tahun:**

```
EC2 Reserved Instance (1 year, no upfront):
- t3.xlarge: $72/bulan (vs $120 on-demand)
- Hemat: $48/bulan = $576/tahun
```

**Cara beli:**
- EC2 Dashboard → Reserved Instances → Purchase Reserved Instances
- Term: 1 year
- Payment option: No upfront (atau partial/all upfront untuk diskon lebih)

#### 4. Optimize Storage

```bash
# Gunakan gp3 instead of gp2 (lebih murah, performa sama)
# gp2 200GB: $20/bulan
# gp3 200GB: $16/bulan (hemat $4/bulan)

# Delete unused snapshots
aws ec2 describe-snapshots --owner-ids self
aws ec2 delete-snapshot --snapshot-id snap-1234567890abcdef0

# Enable S3 Intelligent-Tiering
aws s3api put-bucket-intelligent-tiering-configuration \
  --bucket nexusai-curriculum-raw \
  --id intelligent-tiering-config \
  --intelligent-tiering-configuration file://tiering-config.json
```

#### 5. Optimize Data Transfer

```bash
# Gunakan VPC Endpoints untuk S3 (gratis, no internet gateway)
# EC2 → S3 via VPC Endpoint = $0
# EC2 → S3 via Internet = $0.09/GB

# Create VPC Endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-1234567890abcdef0 \
  --service-name com.amazonaws.ap-southeast-2.s3 \
  --route-table-ids rtb-1234567890abcdef0
```

#### 6. Gunakan CloudFront dengan S3 Origin

```
# Tanpa CloudFront:
S3 GET request: $0.0004/1000 requests
S3 Data transfer: $0.09/GB

# Dengan CloudFront:
CloudFront request: $0.0075/10000 requests
CloudFront transfer: $0.085/GB (first 10TB)

# Hemat untuk high traffic
```

#### 7. Monitoring Budget

```bash
# Setup AWS Budget Alert
# AWS Console → Billing → Budgets → Create budget

# Alert jika biaya > $150/bulan
# Email notification ke: your.email@example.com
```

### Perbandingan Biaya: AWS vs Laptop

#### Laptop (Upgrade Hardware):
```
RAM 16GB upgrade                     : $50-100 (one-time)
SSD 512GB upgrade                    : $50-100 (one-time)
Electricity (24/7, 100W)             : $15/bulan
Internet                             : $30/bulan (existing)
─────────────────────────────────────────────
Initial cost                         : $100-200
Monthly cost                         : $15/bulan
```

#### AWS (Development):
```
Initial cost                         : $0
Monthly cost                         : $139/bulan (full time)
Monthly cost (8 jam/hari)            : $60/bulan
Monthly cost (Spot instance)         : $36/bulan
```

### Rekomendasi Berdasarkan Usage:

1. **Development Intensif (8+ jam/hari):**
   - AWS Spot Instance: $36/bulan
   - Atau upgrade laptop: $100 one-time + $15/bulan

2. **Development Casual (2-4 jam/hari):**
   - AWS On-Demand + auto-stop: $40-60/bulan
   - Start/stop manual saat butuh

3. **Production Testing (24/7):**
   - AWS Reserved Instance: $72/bulan
   - Atau dedicated server lokal


---

## Checklist Setup

### Pre-Launch Checklist

- [ ] AWS Account created and verified
- [ ] IAM user created with proper permissions
- [ ] AWS CLI installed and configured
- [ ] SSH key pair downloaded and saved securely
- [ ] Budget alert configured

### EC2 Setup Checklist

- [ ] EC2 instance launched (t3.xlarge or higher)
- [ ] Security group configured (SSH, port 8000)
- [ ] Elastic IP allocated and associated
- [ ] Successfully connected via SSH
- [ ] System updated (`apt update && apt upgrade`)

### Software Installation Checklist

- [ ] Python 3.10+ installed
- [ ] PostgreSQL installed and configured
- [ ] Redis installed and running
- [ ] System dependencies installed (cmake, poppler, etc.)
- [ ] Virtual environment created

### Application Setup Checklist

- [ ] Repository cloned
- [ ] Python dependencies installed
- [ ] `.env` file configured
- [ ] Database initialized
- [ ] Model downloaded (or configured to auto-download)
- [ ] Application tested and running

### AWS Services Checklist

- [ ] S3 buckets created (curriculum, vkp, model-distribution)
- [ ] S3 bucket policies configured
- [ ] CloudFront distribution created and deployed
- [ ] RDS PostgreSQL setup (if using managed DB)
- [ ] ElastiCache Redis setup (if using managed cache)

### Production Readiness Checklist

- [ ] Systemd service configured and enabled
- [ ] Backup script created and tested
- [ ] Cron job for automatic backup configured
- [ ] CloudWatch monitoring setup (optional)
- [ ] Log rotation configured
- [ ] SSL certificate setup (if needed)

### Remote Development Checklist

- [ ] VS Code Remote SSH extension installed
- [ ] SSH config file configured
- [ ] Successfully connected to EC2 via VS Code
- [ ] Python extension installed in remote
- [ ] Git configured on EC2
- [ ] Port forwarding tested (optional)

---

## Quick Commands Reference

### EC2 Management

```bash
# Connect via SSH
ssh -i openclass-dev-key.pem ubuntu@<EC2-IP>

# Check instance status
aws ec2 describe-instances --instance-ids i-xxxxx

# Stop instance
aws ec2 stop-instances --instance-ids i-xxxxx

# Start instance
aws ec2 start-instances --instance-ids i-xxxxx

# Reboot instance
aws ec2 reboot-instances --instance-ids i-xxxxx
```

### Application Management

```bash
# Start application
sudo systemctl start openclass

# Stop application
sudo systemctl stop openclass

# Restart application
sudo systemctl restart openclass

# Check status
sudo systemctl status openclass

# View logs
sudo tail -f /var/log/openclass/app.log
sudo tail -f /var/log/openclass/error.log

# Manual run (for debugging)
cd ~/projects/openclass-nexus-ai
source openclass-env/bin/activate
python api_server.py
```

### Database Management

```bash
# Connect to PostgreSQL
psql -h localhost -U openclass_user -d openclass_db

# Backup database
pg_dump -h localhost -U openclass_user openclass_db > backup.sql

# Restore database
psql -h localhost -U openclass_user openclass_db < backup.sql

# Check database size
psql -h localhost -U openclass_user -d openclass_db -c "SELECT pg_size_pretty(pg_database_size('openclass_db'));"
```

### Redis Management

```bash
# Check Redis status
redis-cli ping

# Monitor Redis
redis-cli monitor

# Get cache statistics
redis-cli info stats

# Clear cache
redis-cli FLUSHALL

# Check memory usage
redis-cli info memory
```

### S3 Management

```bash
# List buckets
aws s3 ls

# List files in bucket
aws s3 ls s3://nexusai-curriculum-raw/

# Upload file
aws s3 cp local-file.pdf s3://nexusai-curriculum-raw/

# Download file
aws s3 cp s3://nexusai-curriculum-raw/file.pdf ./

# Sync directory
aws s3 sync ./data/raw_dataset/ s3://nexusai-curriculum-raw/

# Delete file
aws s3 rm s3://nexusai-curriculum-raw/file.pdf
```

### System Monitoring

```bash
# Check disk usage
df -h

# Check memory usage
free -h

# Check CPU usage
htop

# Check running processes
ps aux | grep python

# Check network connections
netstat -tulpn | grep 8000

# Check system logs
sudo journalctl -u openclass -f
```

---

## Next Steps

### Setelah Setup Selesai:

1. **Test Aplikasi:**
   - Akses `http://<EC2-IP>:8000`
   - Login dengan demo credentials
   - Test chat functionality
   - Test teacher dashboard
   - Test admin panel

2. **Development Workflow:**
   - Connect VS Code Remote SSH
   - Edit code di VS Code
   - Test changes
   - Commit dan push ke GitHub

3. **Monitoring:**
   - Setup CloudWatch dashboard
   - Configure alerts untuk high CPU/memory
   - Monitor application logs
   - Check backup success

4. **Optimization:**
   - Load testing dengan locust
   - Optimize database queries
   - Enable Redis caching
   - Tune model parameters

5. **Documentation:**
   - Document custom configurations
   - Update team wiki
   - Create runbook untuk common issues

### Resources & Links:

- **AWS Documentation:** https://docs.aws.amazon.com/
- **EC2 Pricing:** https://aws.amazon.com/ec2/pricing/
- **AWS Free Tier:** https://aws.amazon.com/free/
- **AWS Calculator:** https://calculator.aws/
- **VS Code Remote SSH:** https://code.visualstudio.com/docs/remote/ssh

---

## Support & Feedback

Jika ada pertanyaan atau masalah:

1. Check [Troubleshooting](#troubleshooting) section
2. Check application logs: `/var/log/openclass/`
3. Check system logs: `sudo journalctl -u openclass`
4. Create issue di GitHub repository
5. Contact: habibiahmadaziz@gmail.com

---

**Selamat Mengembangkan! 🚀**

*Panduan ini dibuat untuk memudahkan development OpenClass Nexus AI di AWS Cloud*

**Last Updated:** 2025-01-XX  
**Version:** 1.0  
**Author:** OpenClass Development Team

