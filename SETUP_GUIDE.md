# OpenClass Nexus AI - Setup Guide

## Phase 1: Development Environment Setup

This guide will help you set up the development environment for OpenClass Nexus AI following the Phase 1 requirements from the roadmap.

### Prerequisites

- Python 3.10 or higher
- Git
- AWS Account with programmatic access
- 10GB free disk space
- Internet connection for initial setup

### Step 1: Environment Setup

1. **Clone and Navigate to Project**
   ```bash
   cd /path/to/your/project
   # Project structure is already created
   ```

2. **Create Python Virtual Environment**
   ```bash
   # Windows
   python -m venv openclass-env
   openclass-env\Scripts\activate

   # Linux/Mac
   python3 -m venv openclass-env
   source openclass-env/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Step 2: AWS Configuration

1. **Install AWS CLI** (if not already installed)
   ```bash
   pip install awscli
   ```

2. **Configure AWS Credentials**
   ```bash
   aws configure
   ```
   Enter your:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region: `us-east-1`
   - Default output format: `json`

3. **Test AWS Connection**
   ```bash
   aws sts get-caller-identity
   ```

### Step 3: Environment Configuration

1. **Create Environment File**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env File**
   Update the following values in `.env`:
   ```env
   # Replace with your actual values
   AWS_ACCESS_KEY_ID=your_access_key_here
   AWS_SECRET_ACCESS_KEY=your_secret_key_here
   S3_BUCKET_NAME=openclass-nexus-data-your-unique-id
   ```

   **Important**: Replace `your-unique-id` with something unique (e.g., your initials + random numbers)

### Step 4: AWS Infrastructure Setup

1. **Run AWS Setup Script**
   ```bash
   python scripts/setup_aws.py
   ```

   This script will:
   - Create S3 bucket with proper configuration
   - Set up DynamoDB table for usage logs
   - Configure lifecycle policies
   - Set up security settings

2. **Test AWS Connectivity**
   ```bash
   python scripts/test_aws_connection.py
   ```

   This will verify:
   - S3 access
   - Bedrock availability
   - DynamoDB connectivity
   - Cost monitoring setup

### Step 5: Sample Data Setup

1. **Download Sample Educational Content**
   ```bash
   python scripts/download_sample_data.py
   ```

   This will:
   - Create directory structure
   - Download/create sample content
   - Generate dataset inventory
   - Create legal compliance documentation

### Step 6: Verify Setup

After completing all steps, you should have:

```
openclass-nexus/
├── .env                          # Your environment configuration
├── raw_dataset/                  # Sample educational content
│   └── kelas_10/
│       ├── matematika/
│       ├── ipa/
│       └── bahasa_indonesia/
├── dataset_inventory.json        # Content metadata
├── legal_compliance.md          # Legal documentation
└── [all other project files]
```

### Cost Management

**Important**: This setup includes cost protection measures:

1. **Budget Alerts**: Set at $1.00 monthly limit
2. **Lifecycle Policies**: Auto-delete raw files after 30 days
3. **Pay-per-request**: DynamoDB configured for minimal costs
4. **Free Tier**: Utilizes AWS Free Tier where possible

**Estimated Monthly Costs**: $0.50 - $1.00 during development

### Troubleshooting

#### AWS Credentials Issues
```bash
# Check current configuration
aws configure list

# Reconfigure if needed
aws configure
```

#### Permission Errors
Ensure your AWS user has these permissions:
- S3: CreateBucket, PutObject, GetObject
- DynamoDB: CreateTable, DescribeTable
- Bedrock: InvokeModel (in supported regions)
- IAM: Basic read permissions

#### Region Issues
- Bedrock is not available in all regions
- Use `us-east-1` for maximum service availability
- Update `.env` file if you need to change regions

#### Bucket Name Conflicts
S3 bucket names must be globally unique:
1. Edit `.env` file
2. Change `S3_BUCKET_NAME` to something unique
3. Re-run `python scripts/setup_aws.py`

### Next Steps

After successful setup:

1. **Phase 2**: Start implementing data processing pipeline
2. **Development**: Begin working on PDF text extraction
3. **Testing**: Use sample data to test processing scripts

### Development Workflow

1. **Activate Environment**
   ```bash
   # Windows
   openclass-env\Scripts\activate
   
   # Linux/Mac
   source openclass-env/bin/activate
   ```

2. **Run Tests**
   ```bash
   python scripts/test_aws_connection.py
   ```

3. **Start Development**
   - Work on modules in `src/` directory
   - Test with sample data in `raw_dataset/`
   - Use configuration from `config/` modules

### Security Notes

- Never commit `.env` file to version control
- Use IAM roles in production instead of access keys
- Regularly rotate AWS credentials
- Monitor AWS costs through the console

### Support

For issues:
1. Check AWS CloudTrail for API errors
2. Verify IAM permissions
3. Check AWS service status
4. Review error logs in terminal output

---

**Setup Complete!** 🎉

You now have a fully configured development environment for OpenClass Nexus AI Phase 1.