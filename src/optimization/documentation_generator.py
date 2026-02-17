import ast
import inspect
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .models import (
    UserGuide,
    APIDocumentation,
    DeploymentGuide,
    TroubleshootingGuide,
    DocumentationPackage
)
from .config import OptimizationConfig

logger = logging.getLogger(__name__)


class DocumentationGenerator:
    """
    Comprehensive documentation generator for OpenClass Nexus AI system.
    
    This class provides methods to generate user guides, API documentation,
    deployment guides, and troubleshooting documentation in multiple languages.
    """
    
    def __init__(self, config: OptimizationConfig):
        """
        Initialize the documentation generator.
        
        Args:
            config: Optimization configuration containing documentation settings
        """
        self.config = config
        self.project_root = config.project_root
        self.output_dir = config.documentation_output_dir
        self.supported_languages = config.supported_languages
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Documentation generator initialized")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Supported languages: {self.supported_languages}")
    
    def generate_user_guide(self, language: str = "indonesian") -> UserGuide:
        """
        Generate comprehensive user guide in specified language.
        
        Args:
            language: Target language for the guide ("indonesian" or "english")
            
        Returns:
            UserGuide object containing the generated guide
            
        Raises:
            ValueError: If language is not supported
        """
        if language.lower() not in self.supported_languages:
            raise ValueError(f"Language '{language}' not supported. Available: {self.supported_languages}")
        
        language = language.lower()
        logger.info(f"Generating user guide in {language}")
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate content based on language
        if language == "indonesian":
            content = self._generate_indonesian_user_guide()
            sections = [
                "Pendahuluan",
                "Instalasi",
                "Konfigurasi",
                "Penggunaan Dasar",
                "Fitur Lanjutan",
                "Pemecahan Masalah",
                "FAQ"
            ]
        else:  # English
            content = self._generate_english_user_guide()
            sections = [
                "Introduction",
                "Installation",
                "Configuration", 
                "Basic Usage",
                "Advanced Features",
                "Troubleshooting",
                "FAQ"
            ]
        
        # Save to file
        filename = f"user_guide_{language}.md"
        file_path = self.output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"User guide generated: {file_path}")
        
        return UserGuide(
            content=content,
            language=language,
            sections=sections,
            examples_included=True,
            file_path=str(file_path)
        )
    
    def _generate_indonesian_user_guide(self) -> str:
        """Generate Indonesian user guide content."""
        return """# Panduan Pengguna OpenClass Nexus AI

## Pendahuluan

OpenClass Nexus AI adalah platform tutor AI pendidikan yang dirancang khusus untuk mendukung pembelajaran informatika siswa kelas 10 di Indonesia. Sistem ini menggunakan model AI Llama-3.2-3B-Instruct yang telah dioptimalkan untuk konten pendidikan Indonesia dan terintegrasi dengan sumber daya BSE Kemdikbud.

### Fitur Utama
- **Tutor AI Cerdas**: Memberikan jawaban yang disesuaikan dengan kurikulum Indonesia
- **Pemrosesan Bahasa Indonesia**: Mendukung pertanyaan dan jawaban dalam bahasa Indonesia
- **Integrasi BSE**: Menggunakan buku sekolah elektronik Kemdikbud sebagai sumber referensi
- **Performa Tinggi**: Waktu respons di bawah 5 detik dengan penggunaan memori yang efisien
- **Validasi Pendidikan**: Memastikan konten sesuai dengan standar kurikulum

## Instalasi

### Persyaratan Sistem
- Python 3.8 atau lebih tinggi
- RAM minimal 4GB (disarankan 8GB)
- Ruang penyimpanan minimal 10GB
- Koneksi internet untuk unduhan model awal

### Langkah Instalasi

1. **Clone Repository**
   ```bash
   git clone https://github.com/your-org/openclass-nexus-ai.git
   cd openclass-nexus-ai
   ```

2. **Buat Virtual Environment**
   ```bash
   python -m venv openclass-env
   source openclass-env/bin/activate  # Linux/Mac
   # atau
   openclass-env\\Scripts\\activate  # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Konfigurasi Environment**
   ```bash
   cp .env.example .env
   # Edit .env sesuai dengan konfigurasi Anda
   ```

5. **Inisialisasi Database**
   ```bash
   python scripts/setup_phase2_aws.py
   ```

6. **Unduh Model AI**
   ```bash
   python -c "from src.local_inference.model_downloader import ModelDownloader; ModelDownloader().download_model()"
   ```

## Konfigurasi

### File Konfigurasi Utama

#### 1. Environment Variables (.env)
```env
# Model Configuration
MODEL_NAME=meta-llama/Llama-3.2-3B-Instruct
MODEL_CACHE_DIR=./models/cache
MAX_MEMORY_GB=4

# Database Configuration
CHROMA_DB_PATH=./data/vector_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Performance Settings
MAX_RESPONSE_TIME_MS=5000
CONCURRENT_QUERIES=3
BATCH_SIZE=10
```

#### 2. Konfigurasi Model (config/default_config.json)
```json
{
  "model": {
    "name": "meta-llama/Llama-3.2-3B-Instruct",
    "max_length": 2048,
    "temperature": 0.7,
    "top_p": 0.9
  },
  "education": {
    "grade_level": "10",
    "subject": "informatika",
    "curriculum_standard": "kurikulum_merdeka"
  }
}
```

## Penggunaan Dasar

### 1. Memulai Sistem

```bash
# Aktifkan virtual environment
source openclass-env/bin/activate

# Jalankan sistem
python -m src.local_inference.complete_pipeline
```

### 2. Mengajukan Pertanyaan

```python
from src.local_inference.complete_pipeline import CompletePipeline

# Inisialisasi pipeline
pipeline = CompletePipeline()

# Ajukan pertanyaan
question = "Jelaskan konsep algoritma dalam informatika"
response = pipeline.process_query(question)

print(f"Pertanyaan: {question}")
print(f"Jawaban: {response['answer']}")
print(f"Sumber: {response['sources']}")
```

### 3. Contoh Pertanyaan yang Didukung

- **Konsep Dasar**: "Apa itu algoritma dan bagaimana cara kerjanya?"
- **Hardware/Software**: "Jelaskan perbedaan antara hardware dan software"
- **Jaringan**: "Bagaimana cara kerja jaringan komputer?"
- **Keamanan**: "Mengapa keamanan data penting dalam era digital?"
- **Pemrograman**: "Apa itu bahasa pemrograman dan contohnya?"

## Fitur Lanjutan

### 1. Pemrosesan Batch

```python
from src.local_inference.batch_processor import BatchProcessor

processor = BatchProcessor()
questions = [
    "Jelaskan konsep algoritma",
    "Apa itu struktur data?",
    "Bagaimana cara kerja database?"
]

results = processor.process_batch(questions)
for result in results:
    print(f"Q: {result['query']}")
    print(f"A: {result['response']}")
    print("---")
```

### 2. Monitoring Performa

```python
from src.local_inference.performance_monitor import PerformanceMonitor

monitor = PerformanceMonitor()
monitor.start_monitoring()

# Proses pertanyaan Anda
response = pipeline.process_query("Pertanyaan Anda")

metrics = monitor.get_metrics()
print(f"Waktu respons: {metrics['response_time_ms']}ms")
print(f"Penggunaan memori: {metrics['memory_usage_mb']}MB")
```

### 3. Validasi Pendidikan

```python
from src.local_inference.educational_validator import EducationalValidator

validator = EducationalValidator()
validation_result = validator.validate_response(
    query="Jelaskan algoritma",
    response="Algoritma adalah langkah-langkah sistematis...",
    grade_level="10"
)

print(f"Skor kurikulum: {validation_result['curriculum_score']}")
print(f"Kualitas bahasa: {validation_result['language_quality']}")
```

## Pemecahan Masalah

### Masalah Umum dan Solusi

#### 1. Model Tidak Dapat Dimuat
**Gejala**: Error "Model not found" atau "Out of memory"
**Solusi**:
- Pastikan ruang penyimpanan cukup (minimal 10GB)
- Periksa koneksi internet untuk unduhan model
- Kurangi `MAX_MEMORY_GB` di file .env jika RAM terbatas

#### 2. Respons Lambat
**Gejala**: Waktu respons lebih dari 10 detik
**Solusi**:
- Periksa penggunaan CPU dan RAM
- Kurangi `BATCH_SIZE` di konfigurasi
- Pastikan tidak ada proses lain yang menggunakan GPU/CPU intensif

#### 3. Database Vector Tidak Dapat Diakses
**Gejala**: Error "ChromaDB connection failed"
**Solusi**:
- Periksa path `CHROMA_DB_PATH` di .env
- Jalankan ulang inisialisasi database
- Pastikan permission folder database

#### 4. Kualitas Jawaban Rendah
**Gejala**: Jawaban tidak sesuai kurikulum atau tidak akurat
**Solusi**:
- Periksa konfigurasi `grade_level` dan `subject`
- Update database dengan konten BSE terbaru
- Sesuaikan parameter `temperature` dan `top_p`

### Log dan Debugging

#### Mengaktifkan Log Detail
```bash
export LOG_LEVEL=DEBUG
python -m src.local_inference.complete_pipeline
```

#### Lokasi File Log
- Log aplikasi: `./logs/application.log`
- Log performa: `./logs/performance.log`
- Log error: `./logs/error.log`

## FAQ

### Q: Apakah sistem ini dapat digunakan offline?
A: Ya, setelah model dan database diunduh, sistem dapat berjalan sepenuhnya offline.

### Q: Berapa lama waktu setup awal?
A: Setup awal membutuhkan 30-60 menit tergantung kecepatan internet untuk unduhan model.

### Q: Apakah mendukung mata pelajaran selain informatika?
A: Saat ini fokus pada informatika kelas 10, namun dapat diperluas untuk mata pelajaran lain.

### Q: Bagaimana cara memperbarui konten pendidikan?
A: Jalankan script `python scripts/update_educational_content.py` untuk memperbarui database.

### Q: Apakah ada batasan jumlah pertanyaan?
A: Tidak ada batasan, namun performa optimal dengan maksimal 3 pertanyaan bersamaan.

## Dukungan

Untuk bantuan lebih lanjut:
- **Email**: support@openclass-nexus.id
- **GitHub Issues**: https://github.com/your-org/openclass-nexus-ai/issues
- **Dokumentasi**: https://docs.openclass-nexus.id

---

*Panduan ini terakhir diperbarui: {datetime.now().strftime('%d %B %Y')}*
"""

    def _generate_english_user_guide(self) -> str:
        """Generate English user guide content."""
        return """# OpenClass Nexus AI User Guide

## Introduction

OpenClass Nexus AI is an educational AI tutoring platform specifically designed to support grade 10 informatics learning in Indonesia. The system uses the Llama-3.2-3B-Instruct AI model optimized for Indonesian educational content and integrated with BSE Kemdikbud resources.

### Key Features
- **Intelligent AI Tutor**: Provides curriculum-aligned responses for Indonesian education
- **Indonesian Language Processing**: Supports questions and answers in Indonesian
- **BSE Integration**: Uses Kemdikbud electronic school books as reference sources
- **High Performance**: Response times under 5 seconds with efficient memory usage
- **Educational Validation**: Ensures content meets curriculum standards

## Installation

### System Requirements
- Python 3.8 or higher
- Minimum 4GB RAM (8GB recommended)
- Minimum 10GB storage space
- Internet connection for initial model download

### Installation Steps

1. **Clone Repository**
   ```bash
   git clone https://github.com/your-org/openclass-nexus-ai.git
   cd openclass-nexus-ai
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv openclass-env
   source openclass-env/bin/activate  # Linux/Mac
   # or
   openclass-env\\Scripts\\activate  # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env according to your configuration
   ```

5. **Initialize Database**
   ```bash
   python scripts/setup_phase2_aws.py
   ```

6. **Download AI Model**
   ```bash
   python -c "from src.local_inference.model_downloader import ModelDownloader; ModelDownloader().download_model()"
   ```

## Configuration

### Main Configuration Files

#### 1. Environment Variables (.env)
```env
# Model Configuration
MODEL_NAME=meta-llama/Llama-3.2-3B-Instruct
MODEL_CACHE_DIR=./models/cache
MAX_MEMORY_GB=4

# Database Configuration
CHROMA_DB_PATH=./data/vector_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Performance Settings
MAX_RESPONSE_TIME_MS=5000
CONCURRENT_QUERIES=3
BATCH_SIZE=10
```

#### 2. Model Configuration (config/default_config.json)
```json
{
  "model": {
    "name": "meta-llama/Llama-3.2-3B-Instruct",
    "max_length": 2048,
    "temperature": 0.7,
    "top_p": 0.9
  },
  "education": {
    "grade_level": "10",
    "subject": "informatika",
    "curriculum_standard": "kurikulum_merdeka"
  }
}
```

## Basic Usage

### 1. Starting the System

```bash
# Activate virtual environment
source openclass-env/bin/activate

# Run the system
python -m src.local_inference.complete_pipeline
```

### 2. Asking Questions

```python
from src.local_inference.complete_pipeline import CompletePipeline

# Initialize pipeline
pipeline = CompletePipeline()

# Ask a question
question = "Explain the concept of algorithms in informatics"
response = pipeline.process_query(question)

print(f"Question: {question}")
print(f"Answer: {response['answer']}")
print(f"Sources: {response['sources']}")
```

### 3. Supported Question Examples

- **Basic Concepts**: "What is an algorithm and how does it work?"
- **Hardware/Software**: "Explain the difference between hardware and software"
- **Networks**: "How do computer networks work?"
- **Security**: "Why is data security important in the digital era?"
- **Programming**: "What is a programming language and examples?"

## Advanced Features

### 1. Batch Processing

```python
from src.local_inference.batch_processor import BatchProcessor

processor = BatchProcessor()
questions = [
    "Explain the concept of algorithms",
    "What are data structures?",
    "How do databases work?"
]

results = processor.process_batch(questions)
for result in results:
    print(f"Q: {result['query']}")
    print(f"A: {result['response']}")
    print("---")
```

### 2. Performance Monitoring

```python
from src.local_inference.performance_monitor import PerformanceMonitor

monitor = PerformanceMonitor()
monitor.start_monitoring()

# Process your questions
response = pipeline.process_query("Your question")

metrics = monitor.get_metrics()
print(f"Response time: {metrics['response_time_ms']}ms")
print(f"Memory usage: {metrics['memory_usage_mb']}MB")
```

### 3. Educational Validation

```python
from src.local_inference.educational_validator import EducationalValidator

validator = EducationalValidator()
validation_result = validator.validate_response(
    query="Explain algorithms",
    response="An algorithm is a systematic set of steps...",
    grade_level="10"
)

print(f"Curriculum score: {validation_result['curriculum_score']}")
print(f"Language quality: {validation_result['language_quality']}")
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Model Cannot Be Loaded
**Symptoms**: "Model not found" or "Out of memory" errors
**Solutions**:
- Ensure sufficient storage space (minimum 10GB)
- Check internet connection for model download
- Reduce `MAX_MEMORY_GB` in .env file if RAM is limited

#### 2. Slow Response
**Symptoms**: Response time over 10 seconds
**Solutions**:
- Check CPU and RAM usage
- Reduce `BATCH_SIZE` in configuration
- Ensure no other processes are using GPU/CPU intensively

#### 3. Vector Database Inaccessible
**Symptoms**: "ChromaDB connection failed" error
**Solutions**:
- Check `CHROMA_DB_PATH` in .env
- Re-run database initialization
- Ensure database folder permissions

#### 4. Low Answer Quality
**Symptoms**: Answers not curriculum-aligned or inaccurate
**Solutions**:
- Check `grade_level` and `subject` configuration
- Update database with latest BSE content
- Adjust `temperature` and `top_p` parameters

### Logging and Debugging

#### Enable Detailed Logging
```bash
export LOG_LEVEL=DEBUG
python -m src.local_inference.complete_pipeline
```

#### Log File Locations
- Application logs: `./logs/application.log`
- Performance logs: `./logs/performance.log`
- Error logs: `./logs/error.log`

## FAQ

### Q: Can this system be used offline?
A: Yes, after the model and database are downloaded, the system can run completely offline.

### Q: How long does initial setup take?
A: Initial setup takes 30-60 minutes depending on internet speed for model download.

### Q: Does it support subjects other than informatics?
A: Currently focused on grade 10 informatics, but can be extended to other subjects.

### Q: How to update educational content?
A: Run the script `python scripts/update_educational_content.py` to update the database.

### Q: Is there a limit on the number of questions?
A: No limit, but optimal performance with maximum 3 concurrent questions.

## Support

For further assistance:
- **Email**: support@openclass-nexus.id
- **GitHub Issues**: https://github.com/your-org/openclass-nexus-ai/issues
- **Documentation**: https://docs.openclass-nexus.id

---

*This guide was last updated: {datetime.now().strftime('%B %d, %Y')}*
"""
    def create_api_documentation(self) -> APIDocumentation:
        """
        Generate comprehensive API documentation from code.
        
        Returns:
            APIDocumentation object containing the generated documentation
        """
        logger.info("Generating API documentation")
        
        # Scan source code for functions and classes
        api_functions = self._scan_api_functions()
        
        # Generate documentation content
        content = self._generate_api_documentation_content(api_functions)
        
        # Save to file
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = "api_documentation.md"
        file_path = self.output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"API documentation generated: {file_path}")
        
        return APIDocumentation(
            functions_documented=len(api_functions),
            coverage_percentage=self._calculate_coverage_percentage(api_functions),
            examples_included=self.config.include_api_examples,
            file_path=str(file_path)
        )
    
    def _scan_api_functions(self) -> List[Dict[str, Any]]:
        """Scan source code for API functions and classes."""
        api_functions = []
        src_dir = self.project_root / "src"
        
        if not src_dir.exists():
            logger.warning(f"Source directory not found: {src_dir}")
            return api_functions
        
        # Scan Python files in src directory
        for py_file in src_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST to extract functions and classes
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Skip private functions
                        if not node.name.startswith('_'):
                            func_info = self._extract_function_info(node, py_file, content)
                            if func_info:
                                api_functions.append(func_info)
                    
                    elif isinstance(node, ast.ClassDef):
                        class_info = self._extract_class_info(node, py_file, content)
                        if class_info:
                            api_functions.append(class_info)
                            
            except Exception as e:
                logger.warning(f"Error parsing {py_file}: {e}")
                continue
        
        return api_functions
    
    def _extract_function_info(self, node: ast.FunctionDef, file_path: Path, content: str) -> Optional[Dict[str, Any]]:
        """Extract information from a function node."""
        try:
            # Get docstring
            docstring = ast.get_docstring(node) or "No documentation available"
            
            # Get function signature
            args = []
            for arg in node.args.args:
                args.append(arg.arg)
            
            # Get return annotation if available
            return_type = "Any"
            if node.returns:
                return_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else "Any"
            
            return {
                'type': 'function',
                'name': node.name,
                'module': str(file_path.relative_to(self.project_root)).replace('/', '.').replace('.py', ''),
                'docstring': docstring,
                'args': args,
                'return_type': return_type,
                'line_number': node.lineno
            }
        except Exception as e:
            logger.warning(f"Error extracting function info for {node.name}: {e}")
            return None
    
    def _extract_class_info(self, node: ast.ClassDef, file_path: Path, content: str) -> Optional[Dict[str, Any]]:
        """Extract information from a class node."""
        try:
            # Get docstring
            docstring = ast.get_docstring(node) or "No documentation available"
            
            # Get public methods
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                    method_info = self._extract_function_info(item, file_path, content)
                    if method_info:
                        methods.append(method_info)
            
            return {
                'type': 'class',
                'name': node.name,
                'module': str(file_path.relative_to(self.project_root)).replace('/', '.').replace('.py', ''),
                'docstring': docstring,
                'methods': methods,
                'line_number': node.lineno
            }
        except Exception as e:
            logger.warning(f"Error extracting class info for {node.name}: {e}")
            return None
    
    def _calculate_coverage_percentage(self, api_functions: List[Dict[str, Any]]) -> float:
        """Calculate documentation coverage percentage."""
        if not api_functions:
            return 0.0
        
        documented = 0
        total = 0
        
        for func in api_functions:
            total += 1
            if func['docstring'] and func['docstring'] != "No documentation available":
                documented += 1
            
            # Count methods for classes
            if func['type'] == 'class':
                for method in func.get('methods', []):
                    total += 1
                    if method['docstring'] and method['docstring'] != "No documentation available":
                        documented += 1
        
        return (documented / total) * 100 if total > 0 else 0.0
    
    def _generate_api_documentation_content(self, api_functions: List[Dict[str, Any]]) -> str:
        """Generate API documentation content."""
        content = f"""# OpenClass Nexus AI - API Documentation

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

This document provides comprehensive API documentation for OpenClass Nexus AI system components. The system is organized into several modules, each providing specific functionality for the educational AI tutoring platform.

## Table of Contents

"""
        
        # Generate table of contents
        modules = {}
        for func in api_functions:
            module = func['module']
            if module not in modules:
                modules[module] = []
            modules[module].append(func)
        
        for module in sorted(modules.keys()):
            content += f"- [{module}](#{module.replace('.', '-').replace('_', '-')})\n"
        
        content += "\n---\n\n"
        
        # Generate documentation for each module
        for module in sorted(modules.keys()):
            content += f"## {module}\n\n"
            
            module_functions = modules[module]
            
            # Classes first
            classes = [f for f in module_functions if f['type'] == 'class']
            for cls in classes:
                content += self._generate_class_documentation(cls)
            
            # Then standalone functions
            functions = [f for f in module_functions if f['type'] == 'function']
            for func in functions:
                content += self._generate_function_documentation(func)
            
            content += "\n---\n\n"
        
        return content
    
    def _generate_class_documentation(self, cls: Dict[str, Any]) -> str:
        """Generate documentation for a class."""
        content = f"### {cls['name']}\n\n"
        content += f"**Module**: `{cls['module']}`\n\n"
        content += f"**Description**: {cls['docstring']}\n\n"
        
        if cls.get('methods'):
            content += "#### Methods\n\n"
            for method in cls['methods']:
                content += f"##### {method['name']}\n\n"
                content += f"**Arguments**: `{', '.join(method['args'])}`\n\n"
                content += f"**Returns**: `{method['return_type']}`\n\n"
                content += f"**Description**: {method['docstring']}\n\n"
                
                if self.config.include_api_examples:
                    content += self._generate_method_example(cls['name'], method)
        
        return content + "\n"
    
    def _generate_function_documentation(self, func: Dict[str, Any]) -> str:
        """Generate documentation for a function."""
        content = f"### {func['name']}\n\n"
        content += f"**Module**: `{func['module']}`\n\n"
        content += f"**Arguments**: `{', '.join(func['args'])}`\n\n"
        content += f"**Returns**: `{func['return_type']}`\n\n"
        content += f"**Description**: {func['docstring']}\n\n"
        
        if self.config.include_api_examples:
            content += self._generate_function_example(func)
        
        return content + "\n"
    
    def _generate_method_example(self, class_name: str, method: Dict[str, Any]) -> str:
        """Generate usage example for a method."""
        return f"""**Example**:
```python
from {method['module']} import {class_name}

# Initialize the class
instance = {class_name}()

# Call the method
result = instance.{method['name']}({', '.join([f'{arg}=...' for arg in method['args'][1:]])})  # Skip 'self'
print(result)
```

"""
    
    def _generate_function_example(self, func: Dict[str, Any]) -> str:
        """Generate usage example for a function."""
        return f"""**Example**:
```python
from {func['module']} import {func['name']}

# Call the function
result = {func['name']}({', '.join([f'{arg}=...' for arg in func['args']])})
print(result)
```

"""
    
    def build_deployment_guide(self) -> DeploymentGuide:
        """
        Generate production deployment guide.
        
        Returns:
            DeploymentGuide object containing the generated guide
        """
        logger.info("Generating deployment guide")
        
        content = self._generate_deployment_guide_content()
        
        # Save to file
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = "deployment_guide.md"
        file_path = self.output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Deployment guide generated: {file_path}")
        
        return DeploymentGuide(
            content=content,
            environments_covered=["development", "staging", "production", "docker"],
            configuration_examples=[
                "docker-compose.yml",
                "production.env",
                "nginx.conf",
                "systemd.service"
            ],
            file_path=str(file_path)
        )
    
    def _generate_deployment_guide_content(self) -> str:
        """Generate deployment guide content."""
        return f"""# OpenClass Nexus AI - Production Deployment Guide

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

This guide provides comprehensive instructions for deploying OpenClass Nexus AI in production environments. The system supports multiple deployment scenarios including bare metal, containerized, and cloud deployments.

## Prerequisites

### System Requirements
- **CPU**: 4+ cores (8+ recommended)
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 50GB minimum (SSD recommended)
- **OS**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Python**: 3.8+
- **Docker**: 20.10+ (for containerized deployment)

### Network Requirements
- **Inbound**: Port 8000 (API), Port 443 (HTTPS)
- **Outbound**: Internet access for model downloads (initial setup only)
- **Internal**: Database connections if using external databases

## Deployment Options

### Option 1: Bare Metal Deployment

#### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3.8 python3.8-venv python3.8-dev
sudo apt install -y build-essential git curl wget
sudo apt install -y nginx supervisor

# Create application user
sudo useradd -m -s /bin/bash openclass
sudo usermod -aG sudo openclass
```

#### 2. Application Setup

```bash
# Switch to application user
sudo su - openclass

# Clone repository
git clone https://github.com/your-org/openclass-nexus-ai.git
cd openclass-nexus-ai

# Create virtual environment
python3.8 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Setup configuration
cp .env.example .env
# Edit .env with production settings
```

#### 3. Production Configuration

**Environment Variables (.env)**:
```env
# Production Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Model Configuration
MODEL_NAME=meta-llama/Llama-3.2-3B-Instruct
MODEL_CACHE_DIR=/opt/openclass/models
MAX_MEMORY_GB=8

# Database Configuration
CHROMA_DB_PATH=/opt/openclass/data/vector_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Performance Settings
MAX_RESPONSE_TIME_MS=5000
CONCURRENT_QUERIES=5
BATCH_SIZE=20
WORKERS=4

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ORIGINS=https://your-domain.com

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

#### 4. Database Initialization

```bash
# Create data directories
sudo mkdir -p /opt/openclass/data/vector_db
sudo mkdir -p /opt/openclass/models
sudo chown -R openclass:openclass /opt/openclass

# Initialize database
python scripts/setup_phase2_aws.py

# Download and cache models
python -c "from src.local_inference.model_downloader import ModelDownloader; ModelDownloader().download_model()"
```

#### 5. Web Server Configuration

**Nginx Configuration (/etc/nginx/sites-available/openclass)**:
```nginx
server {{
    listen 80;
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # API Proxy
    location /api/ {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }}

    # Static files
    location /static/ {{
        alias /home/openclass/openclass-nexus-ai/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}

    # Health check
    location /health {{
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }}
}}
```

#### 6. Process Management

**Supervisor Configuration (/etc/supervisor/conf.d/openclass.conf)**:
```ini
[program:openclass-api]
command=/home/openclass/openclass-nexus-ai/venv/bin/python -m src.local_inference.complete_pipeline
directory=/home/openclass/openclass-nexus-ai
user=openclass
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/openclass/api.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/home/openclass/openclass-nexus-ai/venv/bin"

[program:openclass-worker]
command=/home/openclass/openclass-nexus-ai/venv/bin/python -m src.local_inference.batch_processor
directory=/home/openclass/openclass-nexus-ai
user=openclass
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/openclass/worker.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/home/openclass/openclass-nexus-ai/venv/bin"
```

### Option 2: Docker Deployment

#### 1. Docker Configuration

**Dockerfile**:
```dockerfile
FROM python:3.8-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd -m -s /bin/bash openclass
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
RUN chown -R openclass:openclass /app

# Switch to application user
USER openclass

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["python", "-m", "src.local_inference.complete_pipeline"]
```

**Docker Compose (docker-compose.yml)**:
```yaml
version: '3.8'

services:
  openclass-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - MODEL_CACHE_DIR=/app/models
      - CHROMA_DB_PATH=/app/data/vector_db
    volumes:
      - ./data:/app/data
      - ./models:/app/models
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - openclass-api
    restart: unless-stopped

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    restart: unless-stopped

volumes:
  grafana-data:
```

#### 2. Container Deployment

```bash
# Build and start services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f openclass-api

# Scale API service
docker-compose up -d --scale openclass-api=3
```

### Option 3: Kubernetes Deployment

#### 1. Kubernetes Manifests

**Deployment (k8s/deployment.yaml)**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openclass-api
  labels:
    app: openclass-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: openclass-api
  template:
    metadata:
      labels:
        app: openclass-api
    spec:
      containers:
      - name: openclass-api
        image: openclass/nexus-ai:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: MODEL_CACHE_DIR
          value: "/app/models"
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        volumeMounts:
        - name: model-cache
          mountPath: /app/models
        - name: data-volume
          mountPath: /app/data
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: model-cache-pvc
      - name: data-volume
        persistentVolumeClaim:
          claimName: data-volume-pvc
```

## Monitoring and Maintenance

### 1. Health Monitoring

```bash
# Check application health
curl http://your-domain.com/health

# Monitor system resources
htop
df -h
free -h

# Check application logs
tail -f /var/log/openclass/api.log
```

### 2. Performance Monitoring

**Prometheus Configuration (prometheus.yml)**:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'openclass-api'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: /metrics
    scrape_interval: 5s
```

### 3. Backup Procedures

```bash
# Backup vector database
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz /opt/openclass/data/

# Backup configuration
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Automated backup script
#!/bin/bash
BACKUP_DIR="/opt/backups/openclass"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/data_$DATE.tar.gz /opt/openclass/data/
cp /home/openclass/openclass-nexus-ai/.env $BACKUP_DIR/config_$DATE.env

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.env" -mtime +7 -delete
```

### 4. Update Procedures

```bash
# Update application
cd /home/openclass/openclass-nexus-ai
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart services
sudo supervisorctl restart openclass-api
sudo supervisorctl restart openclass-worker

# Verify deployment
curl http://localhost:8000/health
```

## Security Considerations

### 1. System Security

- **Firewall**: Configure UFW or iptables to allow only necessary ports
- **SSL/TLS**: Use Let's Encrypt for SSL certificates
- **User Permissions**: Run application with non-root user
- **Updates**: Keep system and dependencies updated

### 2. Application Security

- **Environment Variables**: Store sensitive data in environment variables
- **API Keys**: Rotate API keys regularly
- **Input Validation**: Validate all user inputs
- **Rate Limiting**: Implement rate limiting for API endpoints

### 3. Data Security

- **Encryption**: Encrypt sensitive data at rest
- **Access Control**: Implement proper access controls
- **Audit Logging**: Log all access and modifications
- **Backup Encryption**: Encrypt backup files

## Troubleshooting

### Common Issues

1. **High Memory Usage**: Reduce batch size or concurrent queries
2. **Slow Response Times**: Check CPU usage and model loading
3. **Database Connection Issues**: Verify database paths and permissions
4. **SSL Certificate Issues**: Check certificate validity and renewal

### Performance Tuning

- **CPU Optimization**: Adjust worker processes based on CPU cores
- **Memory Optimization**: Configure model caching and batch sizes
- **I/O Optimization**: Use SSD storage for better performance
- **Network Optimization**: Configure proper load balancing

## Support

For deployment support:
- **Documentation**: https://docs.openclass-nexus.id/deployment
- **Issues**: https://github.com/your-org/openclass-nexus-ai/issues
- **Email**: devops@openclass-nexus.id

---

*This deployment guide was last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    def create_troubleshooting_guide(self) -> TroubleshootingGuide:
        """
        Generate troubleshooting guide with common issues and solutions.
        
        Returns:
            TroubleshootingGuide object containing the generated guide
        """
        logger.info("Generating troubleshooting guide")
        
        content = self._generate_troubleshooting_content()
        
        # Save to file
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = "troubleshooting_guide.md"
        file_path = self.output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Troubleshooting guide generated: {file_path}")
        
        # Count issues and solutions
        issues_count = content.count("### Issue:")
        solutions_count = content.count("**Solution")
        
        return TroubleshootingGuide(
            content=content,
            issues_covered=issues_count,
            solutions_provided=solutions_count,
            file_path=str(file_path)
        )
    
    def _generate_troubleshooting_content(self) -> str:
        """Generate troubleshooting guide content."""
        return f"""# OpenClass Nexus AI - Troubleshooting Guide

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

This guide provides solutions to common issues encountered when using OpenClass Nexus AI. Issues are categorized by component and include step-by-step solutions with diagnostic commands.

## Quick Diagnostic Commands

Before diving into specific issues, run these commands to gather system information:

```bash
# System information
uname -a
python --version
pip list | grep -E "(torch|transformers|chromadb)"

# Resource usage
free -h
df -h
ps aux | grep python

# Application logs
tail -50 /var/log/openclass/api.log
tail -50 /var/log/openclass/error.log
```

## Installation Issues

### Issue: Python Version Compatibility
**Symptoms**: 
- `SyntaxError` during installation
- `ModuleNotFoundError` for core modules
- Package installation failures

**Solution 1 - Check Python Version**:
```bash
python --version
# Should be 3.8 or higher

# If using wrong version, install correct Python
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-dev
```

**Solution 2 - Use Virtual Environment**:
```bash
# Create new virtual environment with correct Python
python3.8 -m venv openclass-env
source openclass-env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Issue: Dependency Installation Failures
**Symptoms**:
- `pip install` fails with compilation errors
- Missing system dependencies
- `wheel` build failures

**Solution 1 - Install System Dependencies**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install build-essential python3-dev
sudo apt install libffi-dev libssl-dev

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel libffi-devel openssl-devel
```

**Solution 2 - Use Pre-compiled Wheels**:
```bash
pip install --only-binary=all -r requirements.txt
# Or install specific problematic packages
pip install --only-binary=torch torch
```

### Issue: Model Download Failures
**Symptoms**:
- `ConnectionError` during model download
- Incomplete model files
- `OSError: Unable to load model`

**Solution 1 - Check Internet Connection**:
```bash
# Test connectivity to Hugging Face
curl -I https://huggingface.co
ping huggingface.co

# Check proxy settings if behind corporate firewall
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

**Solution 2 - Manual Model Download**:
```bash
# Download model manually
python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
model_name = 'meta-llama/Llama-3.2-3B-Instruct'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer.save_pretrained('./models/cache/tokenizer')
model.save_pretrained('./models/cache/model')
"
```

## Runtime Issues

### Issue: High Memory Usage
**Symptoms**:
- System becomes unresponsive
- `OutOfMemoryError` exceptions
- Swap usage at 100%

**Solution 1 - Reduce Model Memory Usage**:
```python
# In your configuration file
MAX_MEMORY_GB = 2  # Reduce from default 4GB
BATCH_SIZE = 5     # Reduce from default 10
CONCURRENT_QUERIES = 1  # Reduce from default 3
```

**Solution 2 - Enable Model Quantization**:
```python
# Add to model configuration
MODEL_CONFIG = {{
    "load_in_8bit": True,  # Enable 8-bit quantization
    "device_map": "auto",
    "torch_dtype": "float16"
}}
```

**Solution 3 - Monitor Memory Usage**:
```bash
# Monitor memory in real-time
watch -n 1 'free -h && ps aux --sort=-%mem | head -10'

# Set memory limits with systemd
sudo systemctl edit openclass-api
# Add:
[Service]
MemoryLimit=6G
MemoryAccounting=yes
```

### Issue: Slow Response Times
**Symptoms**:
- API responses take >10 seconds
- Timeout errors
- Poor user experience

**Solution 1 - Optimize Model Loading**:
```python
# Pre-load model at startup
from src.local_inference.model_manager import ModelManager
manager = ModelManager()
manager.preload_model()  # Load model into memory at startup
```

**Solution 2 - Enable Caching**:
```python
# Enable response caching
ENABLE_RESPONSE_CACHE = True
CACHE_TTL_SECONDS = 3600  # Cache responses for 1 hour
CACHE_MAX_SIZE = 1000     # Maximum cached responses
```

**Solution 3 - Hardware Optimization**:
```bash
# Check CPU usage
htop

# Enable CPU performance mode
sudo cpupower frequency-set -g performance

# Check for thermal throttling
sensors
```

### Issue: Database Connection Failures
**Symptoms**:
- `ChromaDB connection failed`
- `Database locked` errors
- Vector search failures

**Solution 1 - Check Database Path**:
```bash
# Verify database directory exists and has correct permissions
ls -la /path/to/chroma/db
sudo chown -R openclass:openclass /path/to/chroma/db
sudo chmod -R 755 /path/to/chroma/db
```

**Solution 2 - Reset Database**:
```bash
# Backup existing database
cp -r /path/to/chroma/db /path/to/chroma/db.backup

# Reinitialize database
python scripts/setup_phase2_aws.py --reset-db
```

**Solution 3 - Check Database Locks**:
```bash
# Find processes using database files
lsof /path/to/chroma/db/chroma.sqlite3

# Kill hanging processes if necessary
sudo kill -9 <PID>
```

## Performance Issues

### Issue: Poor Educational Content Quality
**Symptoms**:
- Responses not aligned with curriculum
- Incorrect Indonesian grammar
- Missing source attributions

**Solution 1 - Update Educational Database**:
```bash
# Update BSE content
python scripts/update_educational_content.py

# Verify content quality
python scripts/validate_educational_content.py
```

**Solution 2 - Adjust Model Parameters**:
```python
# Fine-tune generation parameters
MODEL_PARAMS = {{
    "temperature": 0.3,      # Lower for more focused responses
    "top_p": 0.8,           # Reduce randomness
    "max_length": 1024,     # Limit response length
    "do_sample": True,
    "pad_token_id": tokenizer.eos_token_id
}}
```

**Solution 3 - Enable Educational Validation**:
```python
# Enable strict educational validation
EDUCATIONAL_VALIDATION = {{
    "enable_curriculum_check": True,
    "min_curriculum_score": 0.85,
    "enable_language_check": True,
    "min_language_score": 0.80,
    "require_source_attribution": True
}}
```

### Issue: Concurrent Processing Failures
**Symptoms**:
- Requests fail under load
- `ThreadPoolExecutor` errors
- Resource contention

**Solution 1 - Adjust Concurrency Settings**:
```python
# Reduce concurrent processing
MAX_CONCURRENT_QUERIES = 2  # Reduce from 3
THREAD_POOL_SIZE = 4        # Adjust based on CPU cores
QUEUE_MAX_SIZE = 100        # Limit request queue
```

**Solution 2 - Implement Request Queuing**:
```python
# Add request queuing with Redis
REDIS_CONFIG = {{
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "max_connections": 10
}}
ENABLE_REQUEST_QUEUE = True
```

## Configuration Issues

### Issue: Environment Variable Problems
**Symptoms**:
- Configuration not loading
- Default values being used
- `KeyError` for required settings

**Solution 1 - Verify Environment File**:
```bash
# Check .env file exists and is readable
ls -la .env
cat .env | grep -v "^#" | grep -v "^$"

# Load environment manually for testing
set -a
source .env
set +a
env | grep -E "(MODEL|CHROMA|MAX_)"
```

**Solution 2 - Validate Configuration**:
```python
# Test configuration loading
from src.optimization.config import OptimizationConfig
config = OptimizationConfig.from_env()
print(config.to_dict())
```

### Issue: Model Configuration Problems
**Symptoms**:
- Wrong model being loaded
- Model parameters ignored
- Inconsistent behavior

**Solution 1 - Check Model Configuration**:
```bash
# Verify model configuration file
cat config/default_config.json | jq .

# Validate JSON syntax
python -m json.tool config/default_config.json
```

**Solution 2 - Reset to Default Configuration**:
```bash
# Backup current configuration
cp config/default_config.json config/default_config.json.backup

# Reset to template
cp config/templates/default_config.json config/default_config.json
```

## Deployment Issues

### Issue: Service Startup Failures
**Symptoms**:
- Service fails to start
- Immediate crashes
- Permission denied errors

**Solution 1 - Check Service Configuration**:
```bash
# Check systemd service status
sudo systemctl status openclass-api
sudo journalctl -u openclass-api -f

# Verify service file
sudo systemctl cat openclass-api
```

**Solution 2 - Fix Permissions**:
```bash
# Fix file permissions
sudo chown -R openclass:openclass /home/openclass/openclass-nexus-ai
sudo chmod +x /home/openclass/openclass-nexus-ai/venv/bin/python

# Fix log directory permissions
sudo mkdir -p /var/log/openclass
sudo chown openclass:openclass /var/log/openclass
```

### Issue: Nginx Proxy Problems
**Symptoms**:
- 502 Bad Gateway errors
- Connection refused
- SSL certificate issues

**Solution 1 - Check Nginx Configuration**:
```bash
# Test nginx configuration
sudo nginx -t

# Check nginx status
sudo systemctl status nginx

# View nginx error logs
sudo tail -f /var/log/nginx/error.log
```

**Solution 2 - Fix SSL Issues**:
```bash
# Renew SSL certificate
sudo certbot renew

# Test SSL configuration
sudo nginx -t
sudo systemctl reload nginx

# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/your-domain.com/fullchain.pem -text -noout
```

## Monitoring and Debugging

### Issue: Missing Logs
**Symptoms**:
- No log files generated
- Empty log files
- Logs not rotating

**Solution 1 - Configure Logging**:
```python
# Enable detailed logging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/openclass/debug.log'),
        logging.StreamHandler()
    ]
)
```

**Solution 2 - Setup Log Rotation**:
```bash
# Configure logrotate
sudo tee /etc/logrotate.d/openclass << EOF
/var/log/openclass/*.log {{
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 openclass openclass
    postrotate
        systemctl reload openclass-api
    endscript
}}
EOF
```

### Issue: Performance Monitoring Problems
**Symptoms**:
- No metrics available
- Prometheus scraping failures
- Grafana dashboard empty

**Solution 1 - Enable Metrics Endpoint**:
```python
# Enable metrics in configuration
ENABLE_METRICS = True
METRICS_PORT = 9090
METRICS_PATH = "/metrics"
```

**Solution 2 - Check Prometheus Configuration**:
```bash
# Test Prometheus configuration
promtool check config prometheus.yml

# Check if metrics endpoint is accessible
curl http://localhost:9090/metrics
```

## Emergency Procedures

### System Recovery
```bash
# Stop all services
sudo systemctl stop openclass-api nginx

# Check system resources
free -h
df -h
ps aux | grep python

# Clear temporary files
sudo rm -rf /tmp/openclass_*
sudo rm -rf /var/cache/openclass/*

# Restart services
sudo systemctl start openclass-api
sudo systemctl start nginx
```

### Database Recovery
```bash
# Stop application
sudo systemctl stop openclass-api

# Restore from backup
cp -r /opt/backups/openclass/data_latest.tar.gz /tmp/
cd /opt/openclass
sudo tar -xzf /tmp/data_latest.tar.gz

# Fix permissions
sudo chown -R openclass:openclass /opt/openclass/data

# Restart application
sudo systemctl start openclass-api
```

## Getting Help

### Diagnostic Information to Collect
When reporting issues, please include:

1. **System Information**:
   ```bash
   uname -a
   python --version
   pip list
   ```

2. **Configuration**:
   ```bash
   cat .env | grep -v "SECRET\|KEY\|PASSWORD"
   cat config/default_config.json
   ```

3. **Logs**:
   ```bash
   tail -100 /var/log/openclass/api.log
   tail -100 /var/log/openclass/error.log
   ```

4. **Resource Usage**:
   ```bash
   free -h
   df -h
   ps aux --sort=-%mem | head -10
   ```

### Support Channels
- **GitHub Issues**: https://github.com/your-org/openclass-nexus-ai/issues
- **Documentation**: https://docs.openclass-nexus.id
- **Email Support**: support@openclass-nexus.id
- **Community Forum**: https://forum.openclass-nexus.id

---

*This troubleshooting guide was last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    def generate_complete_documentation_package(self) -> DocumentationPackage:
        """
        Generate complete documentation package with all guides.
        
        Returns:
            DocumentationPackage containing all generated documentation
        """
        logger.info("Generating complete documentation package")
        
        # Generate all documentation components
        user_guide_id = self.generate_user_guide("indonesian")
        user_guide_en = self.generate_user_guide("english")
        api_docs = self.create_api_documentation()
        deployment_guide = self.build_deployment_guide()
        troubleshooting_guide = self.create_troubleshooting_guide()
        
        # Create examples directory
        examples_dir = self.output_dir / "examples"
        examples_dir.mkdir(exist_ok=True)
        
        # Generate example files
        self._generate_example_files(examples_dir)
        
        logger.info("Complete documentation package generated")
        
        return DocumentationPackage(
            user_guide_path=user_guide_id.file_path,
            api_documentation_path=api_docs.file_path,
            deployment_guide_path=deployment_guide.file_path,
            troubleshooting_guide_path=troubleshooting_guide.file_path,
            examples_directory=str(examples_dir),
            language_versions=["indonesian", "english"]
        )
    
    def _generate_example_files(self, examples_dir: Path):
        """Generate example code files."""
        # Basic usage example
        basic_example = """#!/usr/bin/env python3
\"\"\"
Basic usage example for OpenClass Nexus AI
\"\"\"

from src.local_inference.complete_pipeline import CompletePipeline

def main():
    # Initialize the pipeline
    pipeline = CompletePipeline()
    
    # Example questions
    questions = [
        "Jelaskan konsep algoritma dalam informatika",
        "Apa perbedaan antara hardware dan software?",
        "Bagaimana cara kerja jaringan komputer?"
    ]
    
    # Process each question
    for question in questions:
        print(f"\\nPertanyaan: {question}")
        response = pipeline.process_query(question)
        print(f"Jawaban: {response['answer']}")
        print(f"Sumber: {', '.join(response.get('sources', []))}")
        print("-" * 50)

if __name__ == "__main__":
    main()
"""
        
        with open(examples_dir / "basic_usage.py", 'w', encoding='utf-8') as f:
            f.write(basic_example)
        
        # Batch processing example
        batch_example = """#!/usr/bin/env python3
\"\"\"
Batch processing example for OpenClass Nexus AI
\"\"\"

from src.local_inference.batch_processor import BatchProcessor
from src.local_inference.performance_monitor import PerformanceMonitor

def main():
    # Initialize components
    processor = BatchProcessor()
    monitor = PerformanceMonitor()
    
    # Prepare batch of questions
    questions = [
        "Apa itu struktur data?",
        "Jelaskan konsep database",
        "Bagaimana cara kerja algoritma sorting?",
        "Apa pentingnya keamanan siber?",
        "Jelaskan konsep pemrograman berorientasi objek"
    ]
    
    # Start monitoring
    monitor.start_monitoring()
    
    # Process batch
    print("Memproses batch pertanyaan...")
    results = processor.process_batch(questions)
    
    # Get performance metrics
    metrics = monitor.get_metrics()
    
    # Display results
    for i, result in enumerate(results, 1):
        print(f"\\n{i}. {result['query']}")
        print(f"   Jawaban: {result['response'][:100]}...")
        print(f"   Waktu: {result['response_time_ms']:.2f}ms")
    
    # Display performance summary
    print(f"\\n=== Performance Summary ===")
    print(f"Total waktu: {metrics['total_time_ms']:.2f}ms")
    print(f"Rata-rata per query: {metrics['avg_response_time_ms']:.2f}ms")
    print(f"Penggunaan memori puncak: {metrics['peak_memory_mb']:.2f}MB")

if __name__ == "__main__":
    main()
"""
        
        with open(examples_dir / "batch_processing.py", 'w', encoding='utf-8') as f:
            f.write(batch_example)
        
        # Configuration example
        config_example = """{
  "model": {
    "name": "meta-llama/Llama-3.2-3B-Instruct",
    "max_length": 2048,
    "temperature": 0.7,
    "top_p": 0.9,
    "do_sample": true
  },
  "education": {
    "grade_level": "10",
    "subject": "informatika",
    "curriculum_standard": "kurikulum_merdeka",
    "language": "indonesian"
  },
  "performance": {
    "max_response_time_ms": 5000,
    "max_memory_gb": 4,
    "concurrent_queries": 3,
    "batch_size": 10
  },
  "validation": {
    "enable_curriculum_check": true,
    "min_curriculum_score": 0.85,
    "enable_language_check": true,
    "min_language_score": 0.80,
    "require_source_attribution": true
  }
}"""
        
        with open(examples_dir / "config_example.json", 'w', encoding='utf-8') as f:
            f.write(config_example)
        
        logger.info(f"Example files generated in {examples_dir}")