# OpenClass Nexus AI 🎓

[![License](https://img.shields.io/badge/License-Open%20Educational%20Resources-green)](docs/LEGAL_COMPLIANCE.md)
[![Phase](https://img.shields.io/badge/Status-In%20Development-yellow)](docs/archive/reports/PHASE3_COMPLETION_SUMMARY.md)

**Offline AI Tutor for Indonesian Schools**

OpenClass Nexus AI is an offline-first AI tutoring system designed for schools with limited internet connectivity. It combines local AI inference (Llama 3.2 3B) with a Retrieval-Augmented Generation (RAG) pipeline using BSE Kemdikbud textbooks.

## Key Features
- **Zero Internet Required**: Runs completely offline after initial setup.
- **Low Hardware Requirements**: Optimized for 4GB RAM laptops.
- **Curriculum Aligned**: Answers based on official Indonesian textbooks.
- **Privacy First**: No data leaves the local device during inference.

## Documentation
- **[User Guide](docs/USER_GUIDE.md)**: How to use the AI tutor.
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)**: Setup, installation, and contribution.
- **[System Architecture](docs/SYSTEM_ARCHITECTURE.md)**: Technical design and components.
- **[Legal Compliance](docs/LEGAL_COMPLIANCE.md)**: License and attribution details.

## Quick Start

### Prerequisites
- Python 3.10+
- 4GB+ RAM

### Installation
```bash
git clone https://github.com/habibiahmada/openclass-NexusAI.git

cd openclass-nexus

python -m venv openclass-env

# Activate environment (Windows: openclass-env\Scripts\activate, Linux/Mac: source openclass-env/bin/activate)

pip install -r requirements.txt
```

For detailed setup instructions, see the **[Developer Guide](docs/DEVELOPER_GUIDE.md)**.

## Contributing
We welcome contributions! Please see the [Developer Guide](docs/DEVELOPER_GUIDE.md) for details on our workflow and code standards.

## Developers

OpenClass Nexus AI is developed by our team
![contributors badge](https://readme-contribs.as93.net/contributors/habibiahmada/openclass-NexusAI)


## License
This project uses Open Educational Resources from BSE Kemdikbud. See [Legal Compliance](docs/LEGAL_COMPLIANCE.md) for details.
