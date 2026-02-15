"""
Optimization Module

This module provides comprehensive optimization capabilities for OpenClass Nexus AI,
including project cleanup, system demonstration, documentation generation, and
production readiness validation.
"""

from .models import (
    CleanupReport,
    DemoResponse,
    PerformanceBenchmark,
    DocumentationPackage,
    PerformanceValidation,
    HealthCheckReport,
    DeploymentPackage,
    ConfigurationTemplates,
    DemonstrationReport,
    ValidationResults,
    UserGuide,
    APIDocumentation,
    DeploymentGuide,
    TroubleshootingGuide,
    StructureReport,
    ValidationReport
)

from .config import OptimizationConfig

__all__ = [
    'CleanupReport',
    'DemoResponse', 
    'PerformanceBenchmark',
    'DocumentationPackage',
    'PerformanceValidation',
    'HealthCheckReport',
    'DeploymentPackage',
    'ConfigurationTemplates',
    'DemonstrationReport',
    'ValidationResults',
    'UserGuide',
    'APIDocumentation',
    'DeploymentGuide',
    'TroubleshootingGuide',
    'StructureReport',
    'ValidationReport',
    'OptimizationConfig'
]