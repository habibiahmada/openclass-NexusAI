"""
Documentation Package Executor

This module provides execution capabilities for generating complete documentation
packages including user guides, API documentation, deployment guides, and
troubleshooting documentation in multiple languages.

Implements requirements 3.1, 3.2, 3.3, 3.4, 3.5 from the specification.
"""

import logging
import time
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from .config import OptimizationConfig
from .logger import OptimizationLoggerMixin
from .models import DocumentationPackage, UserGuide, APIDocumentation, DeploymentGuide, TroubleshootingGuide
from .documentation_generator import DocumentationGenerator

logger = logging.getLogger(__name__)


@dataclass
class DocumentationExecutionConfig:
    """Configuration for documentation package execution."""
    
    # Language configuration
    generate_indonesian: bool = True
    generate_english: bool = True
    primary_language: str = "indonesian"
    
    # Content configuration
    include_api_examples: bool = True
    include_code_samples: bool = True
    include_troubleshooting: bool = True
    include_deployment_examples: bool = True
    
    # Generation configuration
    generate_user_guides: bool = True
    generate_api_documentation: bool = True
    generate_deployment_guides: bool = True
    generate_troubleshooting_guides: bool = True
    
    # Output configuration
    create_unified_package: bool = True
    create_language_specific_packages: bool = False
    export_pdf_versions: bool = False  # Future feature
    export_html_versions: bool = True
    
    # Validation configuration
    validate_links: bool = True
    validate_code_examples: bool = True
    validate_completeness: bool = True
    
    # Archive configuration
    create_archive: bool = True
    archive_format: str = "zip"  # "zip" or "tar.gz"


@dataclass
class DocumentationMetrics:
    """Metrics for documentation generation process."""
    
    # Generation metrics
    total_documents_generated: int = 0
    user_guides_generated: int = 0
    api_docs_generated: int = 0
    deployment_guides_generated: int = 0
    troubleshooting_guides_generated: int = 0
    
    # Content metrics
    total_pages_generated: int = 0
    total_code_examples: int = 0
    total_images_included: int = 0
    total_links_validated: int = 0
    
    # Language metrics
    languages_generated: List[str] = field(default_factory=list)
    
    # Quality metrics
    documentation_coverage_percentage: float = 0.0
    api_coverage_percentage: float = 0.0
    validation_errors: int = 0
    validation_warnings: int = 0
    
    # Timing metrics
    generation_start_time: datetime = field(default_factory=datetime.now)
    generation_end_time: Optional[datetime] = None
    total_generation_time_seconds: float = 0.0
    
    def calculate_success_rate(self) -> float:
        """Calculate documentation generation success rate."""
        if self.total_documents_generated == 0:
            return 0.0
        
        expected_docs = 0
        if hasattr(self, '_expected_user_guides'):
            expected_docs += self._expected_user_guides
        if hasattr(self, '_expected_api_docs'):
            expected_docs += self._expected_api_docs
        if hasattr(self, '_expected_deployment_guides'):
            expected_docs += self._expected_deployment_guides
        if hasattr(self, '_expected_troubleshooting_guides'):
            expected_docs += self._expected_troubleshooting_guides
        
        if expected_docs == 0:
            return 100.0
        
        return (self.total_documents_generated / expected_docs) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'total_documents_generated': self.total_documents_generated,
            'user_guides_generated': self.user_guides_generated,
            'api_docs_generated': self.api_docs_generated,
            'deployment_guides_generated': self.deployment_guides_generated,
            'troubleshooting_guides_generated': self.troubleshooting_guides_generated,
            'total_pages_generated': self.total_pages_generated,
            'total_code_examples': self.total_code_examples,
            'total_images_included': self.total_images_included,
            'total_links_validated': self.total_links_validated,
            'languages_generated': self.languages_generated,
            'documentation_coverage_percentage': self.documentation_coverage_percentage,
            'api_coverage_percentage': self.api_coverage_percentage,
            'validation_errors': self.validation_errors,
            'validation_warnings': self.validation_warnings,
            'success_rate_percentage': self.calculate_success_rate(),
            'total_generation_time_seconds': self.total_generation_time_seconds,
            'generation_duration_formatted': self._format_duration()
        }
    
    def _format_duration(self) -> str:
        """Format generation duration as human-readable string."""
        if self.total_generation_time_seconds < 60:
            return f"{self.total_generation_time_seconds:.1f} seconds"
        elif self.total_generation_time_seconds < 3600:
            minutes = self.total_generation_time_seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = self.total_generation_time_seconds / 3600
            return f"{hours:.1f} hours"


class DocumentationPackageExecutor(OptimizationLoggerMixin):
    """
    Documentation package executor for comprehensive documentation generation.
    
    This class provides execution capabilities for generating complete documentation
    packages including user guides, API documentation, deployment guides, and
    troubleshooting documentation in multiple languages.
    """
    
    def __init__(self, 
                 config: Optional[OptimizationConfig] = None,
                 exec_config: Optional[DocumentationExecutionConfig] = None):
        """
        Initialize the documentation package executor.
        
        Args:
            config: Optimization configuration
            exec_config: Documentation execution configuration
        """
        super().__init__()
        self.config = config or OptimizationConfig()
        self.exec_config = exec_config or DocumentationExecutionConfig()
        
        # Initialize documentation generator
        self.documentation_generator = DocumentationGenerator(self.config)
        
        # Metrics tracking
        self.metrics = DocumentationMetrics()
        
        # Generated documents storage
        self.generated_documents: Dict[str, Any] = {
            'user_guides': {},
            'api_documentation': None,
            'deployment_guides': {},
            'troubleshooting_guides': {}
        }
        
        # Output directory
        self.output_dir = self.config.documentation_output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_info("Documentation package executor initialized")
    
    def execute_complete_documentation_generation(self) -> DocumentationPackage:
        """
        Execute complete documentation package generation.
        
        Returns:
            DocumentationPackage with all generated documentation
        """
        self.log_operation_start("complete documentation package generation")
        generation_start_time = time.time()
        
        try:
            # Initialize generation process
            self._initialize_generation_process()
            
            # Generate user guides
            if self.exec_config.generate_user_guides:
                self._generate_user_guides()
            
            # Generate API documentation
            if self.exec_config.generate_api_documentation:
                self._generate_api_documentation()
            
            # Generate deployment guides
            if self.exec_config.generate_deployment_guides:
                self._generate_deployment_guides()
            
            # Generate troubleshooting guides
            if self.exec_config.generate_troubleshooting_guides:
                self._generate_troubleshooting_guides()
            
            # Generate additional resources
            self._generate_additional_resources()
            
            # Validate generated documentation
            if self.exec_config.validate_completeness:
                self._validate_documentation_completeness()
            
            # Create unified package
            documentation_package = self._create_documentation_package()
            
            # Create archives if requested
            if self.exec_config.create_archive:
                self._create_documentation_archives()
            
            # Finalize metrics
            self.metrics.generation_end_time = datetime.now()
            self.metrics.total_generation_time_seconds = time.time() - generation_start_time
            
            # Export generation report
            self._export_generation_report()
            
            generation_duration = time.time() - generation_start_time
            self.log_operation_complete("complete documentation package generation", generation_duration,
                                      documents_generated=self.metrics.total_documents_generated,
                                      languages=len(self.metrics.languages_generated),
                                      success_rate=self.metrics.calculate_success_rate())
            
            return documentation_package
            
        except Exception as e:
            self.log_operation_error("complete documentation package generation", e)
            raise
    
    def _initialize_generation_process(self):
        """Initialize the documentation generation process."""
        try:
            self.log_operation_start("documentation generation initialization")
            
            # Set expected document counts for metrics
            expected_docs = 0
            
            if self.exec_config.generate_user_guides:
                languages = []
                if self.exec_config.generate_indonesian:
                    languages.append("indonesian")
                if self.exec_config.generate_english:
                    languages.append("english")
                expected_docs += len(languages)
                self.metrics._expected_user_guides = len(languages)
            
            if self.exec_config.generate_api_documentation:
                expected_docs += 1
                self.metrics._expected_api_docs = 1
            
            if self.exec_config.generate_deployment_guides:
                expected_docs += 1
                self.metrics._expected_deployment_guides = 1
            
            if self.exec_config.generate_troubleshooting_guides:
                expected_docs += 1
                self.metrics._expected_troubleshooting_guides = 1
            
            self.log_operation_complete("documentation generation initialization",
                                      expected_documents=expected_docs)
            
        except Exception as e:
            self.log_operation_error("documentation generation initialization", e)
            raise
    
    def _generate_user_guides(self):
        """Generate user guides in configured languages."""
        try:
            self.log_operation_start("user guide generation")
            
            languages_to_generate = []
            if self.exec_config.generate_indonesian:
                languages_to_generate.append("indonesian")
            if self.exec_config.generate_english:
                languages_to_generate.append("english")
            
            for language in languages_to_generate:
                try:
                    self.log_info(f"Generating user guide in {language}")
                    
                    user_guide = self.documentation_generator.generate_user_guide(language)
                    self.generated_documents['user_guides'][language] = user_guide
                    
                    self.metrics.user_guides_generated += 1
                    self.metrics.total_documents_generated += 1
                    
                    if language not in self.metrics.languages_generated:
                        self.metrics.languages_generated.append(language)
                    
                    # Count pages (rough estimate based on content length)
                    estimated_pages = len(user_guide.content) // 3000  # ~3000 chars per page
                    self.metrics.total_pages_generated += max(1, estimated_pages)
                    
                    # Count code examples
                    code_examples = user_guide.content.count('```')
                    self.metrics.total_code_examples += code_examples
                    
                    self.log_info(f"User guide generated in {language}: {len(user_guide.content)} characters")
                    
                except Exception as e:
                    self.log_error(f"Failed to generate user guide in {language}: {e}")
                    self.metrics.validation_errors += 1
            
            self.log_operation_complete("user guide generation",
                                      guides_generated=self.metrics.user_guides_generated)
            
        except Exception as e:
            self.log_operation_error("user guide generation", e)
            raise
    
    def _generate_api_documentation(self):
        """Generate API documentation."""
        try:
            self.log_operation_start("API documentation generation")
            
            api_documentation = self.documentation_generator.create_api_documentation()
            self.generated_documents['api_documentation'] = api_documentation
            
            self.metrics.api_docs_generated += 1
            self.metrics.total_documents_generated += 1
            self.metrics.api_coverage_percentage = api_documentation.coverage_percentage
            
            # Count pages and examples
            estimated_pages = 10  # API docs are typically substantial
            self.metrics.total_pages_generated += estimated_pages
            
            if api_documentation.examples_included:
                self.metrics.total_code_examples += api_documentation.functions_documented
            
            self.log_operation_complete("API documentation generation",
                                      functions_documented=api_documentation.functions_documented,
                                      coverage_percentage=api_documentation.coverage_percentage)
            
        except Exception as e:
            self.log_operation_error("API documentation generation", e)
            self.metrics.validation_errors += 1
            raise
    
    def _generate_deployment_guides(self):
        """Generate deployment guides."""
        try:
            self.log_operation_start("deployment guide generation")
            
            deployment_guide = self.documentation_generator.build_deployment_guide()
            self.generated_documents['deployment_guides']['production'] = deployment_guide
            
            self.metrics.deployment_guides_generated += 1
            self.metrics.total_documents_generated += 1
            
            # Count pages and examples
            estimated_pages = len(deployment_guide.content) // 3000
            self.metrics.total_pages_generated += max(1, estimated_pages)
            
            # Count configuration examples
            config_examples = len(deployment_guide.configuration_examples)
            self.metrics.total_code_examples += config_examples
            
            self.log_operation_complete("deployment guide generation",
                                      environments_covered=len(deployment_guide.environments_covered),
                                      config_examples=config_examples)
            
        except Exception as e:
            self.log_operation_error("deployment guide generation", e)
            self.metrics.validation_errors += 1
            raise
    
    def _generate_troubleshooting_guides(self):
        """Generate troubleshooting guides."""
        try:
            self.log_operation_start("troubleshooting guide generation")
            
            troubleshooting_guide = self.documentation_generator.create_troubleshooting_guide()
            self.generated_documents['troubleshooting_guides']['general'] = troubleshooting_guide
            
            self.metrics.troubleshooting_guides_generated += 1
            self.metrics.total_documents_generated += 1
            
            # Count pages and examples
            estimated_pages = len(troubleshooting_guide.content) // 3000
            self.metrics.total_pages_generated += max(1, estimated_pages)
            
            # Count code examples (solutions often include code)
            code_examples = troubleshooting_guide.content.count('```')
            self.metrics.total_code_examples += code_examples
            
            self.log_operation_complete("troubleshooting guide generation",
                                      issues_covered=troubleshooting_guide.issues_covered,
                                      solutions_provided=troubleshooting_guide.solutions_provided)
            
        except Exception as e:
            self.log_operation_error("troubleshooting guide generation", e)
            self.metrics.validation_errors += 1
            raise
    
    def _generate_additional_resources(self):
        """Generate additional documentation resources."""
        try:
            self.log_operation_start("additional resources generation")
            
            # Create examples directory
            examples_dir = self.output_dir / "examples"
            examples_dir.mkdir(exist_ok=True)
            
            # Generate configuration examples
            self._generate_configuration_examples(examples_dir)
            
            # Generate code examples
            if self.exec_config.include_code_samples:
                self._generate_code_examples(examples_dir)
            
            # Generate README files
            self._generate_readme_files()
            
            # Generate index files
            self._generate_index_files()
            
            self.log_operation_complete("additional resources generation")
            
        except Exception as e:
            self.log_operation_error("additional resources generation", e)
            self.metrics.validation_warnings += 1
    
    def _generate_configuration_examples(self, examples_dir: Path):
        """Generate configuration example files."""
        try:
            config_dir = examples_dir / "configuration"
            config_dir.mkdir(exist_ok=True)
            
            # Environment configuration example
            env_example = """# OpenClass Nexus AI - Environment Configuration Example
# Copy this file to .env and modify values as needed

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

# Educational Settings
GRADE_LEVEL=10
SUBJECT=informatika
CURRICULUM_STANDARD=kurikulum_merdeka
LANGUAGE=indonesian

# Validation Settings
ENABLE_CURRICULUM_CHECK=true
MIN_CURRICULUM_SCORE=0.85
ENABLE_LANGUAGE_CHECK=true
MIN_LANGUAGE_SCORE=0.80
REQUIRE_SOURCE_ATTRIBUTION=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/application.log

# Security (set these in production)
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:3000
"""
            
            with open(config_dir / "environment_example.env", 'w', encoding='utf-8') as f:
                f.write(env_example)
            
            # Model configuration example
            model_config = {
                "model": {
                    "name": "meta-llama/Llama-3.2-3B-Instruct",
                    "max_length": 2048,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "do_sample": True,
                    "pad_token_id": 128001
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
                    "enable_curriculum_check": True,
                    "min_curriculum_score": 0.85,
                    "enable_language_check": True,
                    "min_language_score": 0.80,
                    "require_source_attribution": True
                }
            }
            
            with open(config_dir / "model_config_example.json", 'w', encoding='utf-8') as f:
                json.dump(model_config, f, indent=2, ensure_ascii=False)
            
            self.metrics.total_code_examples += 2
            
        except Exception as e:
            self.log_error(f"Failed to generate configuration examples: {e}")
    
    def _generate_code_examples(self, examples_dir: Path):
        """Generate code example files."""
        try:
            code_dir = examples_dir / "code"
            code_dir.mkdir(exist_ok=True)
            
            # Basic usage example
            basic_usage = '''#!/usr/bin/env python3
"""
Basic usage example for OpenClass Nexus AI
"""

from src.local_inference.complete_pipeline import CompletePipeline

def main():
    """Demonstrate basic usage of OpenClass Nexus AI."""
    # Initialize the pipeline
    pipeline = CompletePipeline()
    
    # Example questions in Indonesian
    questions = [
        "Jelaskan konsep algoritma dalam informatika",
        "Apa perbedaan antara hardware dan software?",
        "Bagaimana cara kerja jaringan komputer?"
    ]
    
    # Process each question
    for i, question in enumerate(questions, 1):
        print(f"\\n{i}. Pertanyaan: {question}")
        
        try:
            response = pipeline.process_query(question)
            print(f"   Jawaban: {response['answer'][:200]}...")
            
            if 'sources' in response:
                print(f"   Sumber: {', '.join(response['sources'][:2])}")
                
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    main()
'''
            
            with open(code_dir / "basic_usage.py", 'w', encoding='utf-8') as f:
                f.write(basic_usage)
            
            # Batch processing example
            batch_example = '''#!/usr/bin/env python3
"""
Batch processing example for OpenClass Nexus AI
"""

from src.local_inference.batch_processor import BatchProcessor
from src.local_inference.performance_monitor import PerformanceMonitor

def main():
    """Demonstrate batch processing capabilities."""
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
    
    print("Memproses batch pertanyaan...")
    
    # Start monitoring
    monitor.start_monitoring()
    
    try:
        # Process batch
        results = processor.process_batch(questions)
        
        # Get performance metrics
        metrics = monitor.get_metrics()
        
        # Display results
        print(f"\\n=== Hasil Batch Processing ===")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['query']}")
            print(f"   Jawaban: {result['response'][:100]}...")
            print(f"   Waktu: {result.get('response_time_ms', 0):.2f}ms")
        
        # Display performance summary
        print(f"\\n=== Ringkasan Performa ===")
        print(f"Total waktu: {metrics.get('total_time_ms', 0):.2f}ms")
        print(f"Rata-rata per query: {metrics.get('avg_response_time_ms', 0):.2f}ms")
        print(f"Penggunaan memori puncak: {metrics.get('peak_memory_mb', 0):.2f}MB")
        
    except Exception as e:
        print(f"Error dalam batch processing: {e}")
    
    finally:
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()
'''
            
            with open(code_dir / "batch_processing.py", 'w', encoding='utf-8') as f:
                f.write(batch_example)
            
            self.metrics.total_code_examples += 2
            
        except Exception as e:
            self.log_error(f"Failed to generate code examples: {e}")
    
    def _generate_readme_files(self):
        """Generate README files for documentation structure."""
        try:
            # Main README for documentation
            main_readme = f"""# OpenClass Nexus AI - Documentation Package

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

This documentation package contains comprehensive guides and references for OpenClass Nexus AI, an educational AI tutoring platform designed for Indonesian grade 10 informatics education.

## Documentation Structure

### User Guides
- `user_guide_indonesian.md` - Panduan pengguna dalam bahasa Indonesia
- `user_guide_english.md` - User guide in English

### Technical Documentation
- `api_documentation.md` - Complete API reference with examples
- `deployment_guide.md` - Production deployment instructions
- `troubleshooting_guide.md` - Common issues and solutions

### Examples and Resources
- `examples/` - Code examples and configuration templates
- `examples/configuration/` - Configuration file examples
- `examples/code/` - Python code examples

## Quick Start

1. **Installation**: Follow the installation guide in the user guide
2. **Configuration**: Use examples in `examples/configuration/`
3. **Basic Usage**: See code examples in `examples/code/`
4. **Deployment**: Follow the deployment guide for production setup

## Languages Supported

- **Indonesian (Bahasa Indonesia)** - Primary language for educational content
- **English** - Technical documentation and international users

## System Requirements

- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- 10GB storage space
- Internet connection for initial setup

## Support

- **Documentation Issues**: Check troubleshooting guide
- **Technical Support**: See deployment guide for support contacts
- **Educational Content**: Aligned with Indonesian curriculum standards

## Version Information

- **Documentation Version**: Phase 3 Optimization
- **System Version**: OpenClass Nexus AI v3.0
- **Last Updated**: {datetime.now().strftime('%Y-%m-%d')}

---

*This documentation package was generated automatically by the OpenClass Nexus AI optimization system.*
"""
            
            with open(self.output_dir / "README.md", 'w', encoding='utf-8') as f:
                f.write(main_readme)
            
            # Examples README
            examples_readme = """# Examples and Configuration Templates

This directory contains practical examples and configuration templates for OpenClass Nexus AI.

## Directory Structure

- `configuration/` - Configuration file examples
  - `environment_example.env` - Environment variables template
  - `model_config_example.json` - Model configuration template

- `code/` - Python code examples
  - `basic_usage.py` - Basic system usage example
  - `batch_processing.py` - Batch processing example

## Usage

1. Copy configuration templates to your project root
2. Modify configuration values according to your environment
3. Run code examples to test system functionality
4. Refer to user guides for detailed explanations

## Configuration Notes

- Always use environment variables for sensitive data
- Test configurations in development before production deployment
- Monitor system performance and adjust settings as needed

## Code Examples

All code examples are self-contained and include error handling. They demonstrate:

- Basic query processing
- Batch operations
- Performance monitoring
- Error handling patterns

Run examples with: `python examples/code/example_name.py`
"""
            
            examples_dir = self.output_dir / "examples"
            with open(examples_dir / "README.md", 'w', encoding='utf-8') as f:
                f.write(examples_readme)
            
        except Exception as e:
            self.log_error(f"Failed to generate README files: {e}")
    
    def _generate_index_files(self):
        """Generate index files for easy navigation."""
        try:
            # HTML index for web viewing
            html_index = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenClass Nexus AI - Documentation Index</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .section {{ margin-bottom: 30px; }}
        .doc-list {{ list-style: none; padding: 0; }}
        .doc-item {{ background: #f8f9fa; margin: 10px 0; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; }}
        .doc-item h3 {{ margin: 0 0 10px 0; color: #007bff; }}
        .doc-item p {{ margin: 0; color: #666; }}
        .doc-item a {{ color: #007bff; text-decoration: none; }}
        .doc-item a:hover {{ text-decoration: underline; }}
        .stats {{ background: #e9ecef; padding: 15px; border-radius: 6px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>OpenClass Nexus AI</h1>
            <h2>Documentation Package</h2>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="section">
            <h2>User Guides</h2>
            <ul class="doc-list">
                <li class="doc-item">
                    <h3><a href="user_guide_indonesian.md">Panduan Pengguna (Indonesian)</a></h3>
                    <p>Panduan lengkap penggunaan sistem dalam bahasa Indonesia</p>
                </li>
                <li class="doc-item">
                    <h3><a href="user_guide_english.md">User Guide (English)</a></h3>
                    <p>Complete system usage guide in English</p>
                </li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Technical Documentation</h2>
            <ul class="doc-list">
                <li class="doc-item">
                    <h3><a href="api_documentation.md">API Documentation</a></h3>
                    <p>Complete API reference with function descriptions and examples</p>
                </li>
                <li class="doc-item">
                    <h3><a href="deployment_guide.md">Deployment Guide</a></h3>
                    <p>Production deployment instructions and configuration</p>
                </li>
                <li class="doc-item">
                    <h3><a href="troubleshooting_guide.md">Troubleshooting Guide</a></h3>
                    <p>Common issues, solutions, and debugging procedures</p>
                </li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Examples and Resources</h2>
            <ul class="doc-list">
                <li class="doc-item">
                    <h3><a href="examples/">Examples Directory</a></h3>
                    <p>Code examples and configuration templates</p>
                </li>
                <li class="doc-item">
                    <h3><a href="README.md">Documentation README</a></h3>
                    <p>Overview and quick start guide</p>
                </li>
            </ul>
        </div>
        
        <div class="stats">
            <h3>Package Statistics</h3>
            <p><strong>Total Documents:</strong> {self.metrics.total_documents_generated}</p>
            <p><strong>Languages:</strong> {', '.join(self.metrics.languages_generated)}</p>
            <p><strong>Code Examples:</strong> {self.metrics.total_code_examples}</p>
            <p><strong>Estimated Pages:</strong> {self.metrics.total_pages_generated}</p>
        </div>
    </div>
</body>
</html>"""
            
            with open(self.output_dir / "index.html", 'w', encoding='utf-8') as f:
                f.write(html_index)
            
        except Exception as e:
            self.log_error(f"Failed to generate index files: {e}")
    
    def _validate_documentation_completeness(self):
        """Validate that all required documentation was generated."""
        try:
            self.log_operation_start("documentation completeness validation")
            
            validation_errors = 0
            validation_warnings = 0
            
            # Check user guides
            if self.exec_config.generate_user_guides:
                if self.exec_config.generate_indonesian and 'indonesian' not in self.generated_documents['user_guides']:
                    validation_errors += 1
                    self.log_error("Indonesian user guide not generated")
                
                if self.exec_config.generate_english and 'english' not in self.generated_documents['user_guides']:
                    validation_errors += 1
                    self.log_error("English user guide not generated")
            
            # Check API documentation
            if self.exec_config.generate_api_documentation and not self.generated_documents['api_documentation']:
                validation_errors += 1
                self.log_error("API documentation not generated")
            
            # Check deployment guides
            if self.exec_config.generate_deployment_guides and not self.generated_documents['deployment_guides']:
                validation_errors += 1
                self.log_error("Deployment guides not generated")
            
            # Check troubleshooting guides
            if self.exec_config.generate_troubleshooting_guides and not self.generated_documents['troubleshooting_guides']:
                validation_errors += 1
                self.log_error("Troubleshooting guides not generated")
            
            # Validate file existence
            for doc_type, docs in self.generated_documents.items():
                if isinstance(docs, dict):
                    for doc_name, doc in docs.items():
                        if hasattr(doc, 'file_path') and not Path(doc.file_path).exists():
                            validation_warnings += 1
                            self.log_warning(f"Generated file not found: {doc.file_path}")
                elif docs and hasattr(docs, 'file_path') and not Path(docs.file_path).exists():
                    validation_warnings += 1
                    self.log_warning(f"Generated file not found: {docs.file_path}")
            
            self.metrics.validation_errors = validation_errors
            self.metrics.validation_warnings = validation_warnings
            
            self.log_operation_complete("documentation completeness validation",
                                      validation_errors=validation_errors,
                                      validation_warnings=validation_warnings)
            
        except Exception as e:
            self.log_operation_error("documentation completeness validation", e)
            self.metrics.validation_errors += 1
    
    def _create_documentation_package(self) -> DocumentationPackage:
        """Create the final documentation package."""
        try:
            self.log_operation_start("documentation package creation")
            
            # Determine primary paths
            user_guide_path = ""
            if self.generated_documents['user_guides']:
                primary_lang = self.exec_config.primary_language
                if primary_lang in self.generated_documents['user_guides']:
                    user_guide_path = self.generated_documents['user_guides'][primary_lang].file_path
                else:
                    # Use first available language
                    first_guide = next(iter(self.generated_documents['user_guides'].values()))
                    user_guide_path = first_guide.file_path
            
            api_documentation_path = ""
            if self.generated_documents['api_documentation']:
                api_documentation_path = self.generated_documents['api_documentation'].file_path
            
            deployment_guide_path = ""
            if self.generated_documents['deployment_guides']:
                first_guide = next(iter(self.generated_documents['deployment_guides'].values()))
                deployment_guide_path = first_guide.file_path
            
            troubleshooting_guide_path = ""
            if self.generated_documents['troubleshooting_guides']:
                first_guide = next(iter(self.generated_documents['troubleshooting_guides'].values()))
                troubleshooting_guide_path = first_guide.file_path
            
            # Create documentation package
            documentation_package = DocumentationPackage(
                user_guide_path=user_guide_path,
                api_documentation_path=api_documentation_path,
                deployment_guide_path=deployment_guide_path,
                troubleshooting_guide_path=troubleshooting_guide_path,
                examples_directory=str(self.output_dir / "examples"),
                language_versions=self.metrics.languages_generated.copy()
            )
            
            self.log_operation_complete("documentation package creation",
                                      languages=len(documentation_package.language_versions))
            
            return documentation_package
            
        except Exception as e:
            self.log_operation_error("documentation package creation", e)
            raise
    
    def _create_documentation_archives(self):
        """Create archive files of the documentation package."""
        try:
            self.log_operation_start("documentation archive creation")
            
            archive_name = f"openclass_nexus_ai_documentation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if self.exec_config.archive_format == "zip":
                import zipfile
                
                archive_path = self.output_dir.parent / f"{archive_name}.zip"
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in self.output_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(self.output_dir.parent)
                            zipf.write(file_path, arcname)
                
                self.log_info(f"ZIP archive created: {archive_path}")
                
            elif self.exec_config.archive_format == "tar.gz":
                import tarfile
                
                archive_path = self.output_dir.parent / f"{archive_name}.tar.gz"
                with tarfile.open(archive_path, 'w:gz') as tarf:
                    tarf.add(self.output_dir, arcname=self.output_dir.name)
                
                self.log_info(f"TAR.GZ archive created: {archive_path}")
            
            self.log_operation_complete("documentation archive creation")
            
        except Exception as e:
            self.log_operation_error("documentation archive creation", e)
            self.metrics.validation_warnings += 1
    
    def _export_generation_report(self):
        """Export documentation generation report."""
        try:
            report_data = {
                'generation_summary': {
                    'timestamp': datetime.now().isoformat(),
                    'total_documents_generated': self.metrics.total_documents_generated,
                    'success_rate_percentage': self.metrics.calculate_success_rate(),
                    'total_generation_time_seconds': self.metrics.total_generation_time_seconds,
                    'languages_generated': self.metrics.languages_generated
                },
                'detailed_metrics': self.metrics.to_dict(),
                'generated_documents': {
                    'user_guides': list(self.generated_documents['user_guides'].keys()),
                    'api_documentation': bool(self.generated_documents['api_documentation']),
                    'deployment_guides': list(self.generated_documents['deployment_guides'].keys()),
                    'troubleshooting_guides': list(self.generated_documents['troubleshooting_guides'].keys())
                },
                'configuration': {
                    'generate_indonesian': self.exec_config.generate_indonesian,
                    'generate_english': self.exec_config.generate_english,
                    'include_api_examples': self.exec_config.include_api_examples,
                    'include_code_samples': self.exec_config.include_code_samples,
                    'create_archive': self.exec_config.create_archive
                }
            }
            
            report_file = self.output_dir / "generation_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self.log_info(f"Generation report exported to {report_file}")
            
        except Exception as e:
            self.log_error(f"Failed to export generation report: {e}")


# Convenience function for running documentation generation
def run_documentation_generation(
    config: Optional[OptimizationConfig] = None,
    exec_config: Optional[DocumentationExecutionConfig] = None
) -> DocumentationPackage:
    """
    Run complete documentation package generation.
    
    Args:
        config: Optimization configuration
        exec_config: Documentation execution configuration
    
    Returns:
        DocumentationPackage with all generated documentation
    """
    executor = DocumentationPackageExecutor(config, exec_config)
    return executor.execute_complete_documentation_generation()


# Example usage
def example_documentation_execution():
    """Example of how to use the documentation executor."""
    print("OpenClass Nexus AI - Documentation Package Executor Example")
    print("This example shows how to generate complete documentation packages")
    
    # Create custom execution configuration
    exec_config = DocumentationExecutionConfig(
        generate_indonesian=True,
        generate_english=True,
        include_code_samples=True,
        create_archive=True,
        export_html_versions=True
    )
    
    # Run documentation generation
    package = run_documentation_generation(exec_config=exec_config)
    
    print(f"\nDocumentation generation completed")
    print(f"Languages: {', '.join(package.language_versions)}")
    print(f"User guide: {package.user_guide_path}")
    print(f"API docs: {package.api_documentation_path}")
    print(f"Deployment guide: {package.deployment_guide_path}")
    print(f"Troubleshooting guide: {package.troubleshooting_guide_path}")
    print(f"Examples: {package.examples_directory}")


if __name__ == "__main__":
    example_documentation_execution()