"""
System Validation Executor

This module executes comprehensive system validation including performance requirements,
health checks, and production readiness assessment.
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from .production_validator import ProductionReadinessValidator
from .models import PerformanceValidation, HealthCheckReport, ValidationReport
from .config import OptimizationConfig

logger = logging.getLogger(__name__)


class SystemValidator:
    """Executes comprehensive system validation for production readiness."""
    
    def __init__(self, config: OptimizationConfig):
        """Initialize the system validator."""
        self.config = config
        self.output_dir = config.optimization_output_dir
        self.validator = ProductionReadinessValidator(config)
        
        logger.info("System validator initialized")
    
    def execute_comprehensive_validation(self) -> ValidationReport:
        """Execute comprehensive system validation."""
        logger.info("Starting comprehensive system validation")
        
        validation_results = {}
        issues_found = []
        recommendations = []
        components_validated = 0
        
        try:
            # 1. Performance Requirements Validation
            logger.info("Validating performance requirements...")
            performance_validation = self.validator.validate_performance_requirements()
            validation_results['performance'] = performance_validation.to_dict()
            components_validated += 1
            
            if not performance_validation.response_time_compliant:
                issues_found.append("Response time exceeds 5 second threshold")
                recommendations.append("Optimize model inference or increase hardware resources")
            
            if not performance_validation.memory_usage_compliant:
                issues_found.append("Memory usage exceeds 4GB threshold")
                recommendations.append("Optimize memory usage or increase available RAM")
            
            if not performance_validation.curriculum_alignment_compliant:
                issues_found.append("Curriculum alignment below 85% threshold")
                recommendations.append("Improve educational content validation and model fine-tuning")
            
            # 2. System Health Check
            logger.info("Running comprehensive health check...")
            health_check = self.validator.run_comprehensive_health_check()
            validation_results['health_check'] = health_check.to_dict()
            components_validated += 1
            
            if not health_check.overall_health:
                issues_found.extend(health_check.issues_found)
                recommendations.extend(health_check.recommendations)
            
            # 3. Component Status Evaluation
            logger.info("Evaluating component status...")
            component_status = self._evaluate_component_status(health_check)
            validation_results['component_status'] = component_status
            components_validated += 1
            
            # 4. System Integration Test
            logger.info("Running system integration test...")
            integration_results = self._run_integration_test()
            validation_results['integration'] = integration_results
            components_validated += 1
            
            if not integration_results.get('passed', False):
                issues_found.append("System integration test failed")
                recommendations.append("Check component interactions and data flow")
            
            # Calculate overall validation score
            performance_score = performance_validation.overall_score
            health_score = 1.0 if health_check.overall_health else 0.0
            integration_score = 1.0 if integration_results.get('passed', False) else 0.0
            
            overall_score = (performance_score + health_score + integration_score) / 3
            validation_passed = overall_score >= 0.8  # 80% threshold
            
            # Create validation report
            validation_report = ValidationReport(
                components_validated=components_validated,
                validation_passed=validation_passed,
                issues_found=issues_found,
                recommendations=recommendations,
                overall_score=overall_score
            )
            
            # Save validation results
            self._save_validation_results(validation_results, validation_report)
            
            logger.info(f"Comprehensive validation completed. Score: {overall_score:.2f}")
            return validation_report
            
        except Exception as e:
            logger.error(f"Comprehensive validation failed: {e}")
            return ValidationReport(
                components_validated=components_validated,
                validation_passed=False,
                issues_found=[f"Validation failed: {str(e)}"],
                recommendations=["Check system configuration and dependencies"],
                overall_score=0.0
            )
    
    def _evaluate_component_status(self, health_check: HealthCheckReport) -> Dict[str, Any]:
        """Evaluate detailed component status."""
        component_evaluation = {
            'total_components': len(health_check.component_status),
            'healthy_components': sum(health_check.component_status.values()),
            'unhealthy_components': len(health_check.component_status) - sum(health_check.component_status.values()),
            'component_details': health_check.component_status,
            'health_percentage': (sum(health_check.component_status.values()) / len(health_check.component_status)) * 100
        }
        
        return component_evaluation
    
    def _run_integration_test(self) -> Dict[str, Any]:
        """Run system integration test."""
        try:
            from src.local_inference.complete_pipeline import CompletePipeline
            from src.local_inference.config_manager import ConfigurationManager
            
            # Initialize complete pipeline
            config_manager = ConfigurationManager()
            pipeline = CompletePipeline(config_manager)
            
            # Test end-to-end processing
            test_query = "Jelaskan konsep algoritma dalam informatika untuk siswa kelas 10"
            
            start_time = datetime.now()
            result = pipeline.process_query(test_query)
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds()
            
            # Validate result structure
            has_response = bool(result and len(str(result)) > 0)
            response_length = len(str(result)) if result else 0
            
            integration_results = {
                'passed': has_response and processing_time < 10.0,  # 10 second timeout
                'processing_time_seconds': processing_time,
                'response_generated': has_response,
                'response_length': response_length,
                'test_query': test_query,
                'timestamp': datetime.now().isoformat()
            }
            
            return integration_results
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            return {
                'passed': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _save_validation_results(self, validation_results: Dict[str, Any], 
                                validation_report: ValidationReport):
        """Save validation results to files."""
        try:
            # Create validation output directory
            validation_dir = self.output_dir / "validation_results"
            validation_dir.mkdir(exist_ok=True)
            
            # Save detailed validation results
            results_file = validation_dir / "comprehensive_validation_results.json"
            with open(results_file, 'w') as f:
                json.dump(validation_results, f, indent=2, default=str)
            
            # Save validation report
            report_file = validation_dir / "validation_report.json"
            with open(report_file, 'w') as f:
                json.dump(validation_report.to_dict(), f, indent=2, default=str)
            
            # Create human-readable summary
            summary_file = validation_dir / "validation_summary.md"
            summary_content = self._generate_validation_summary(validation_results, validation_report)
            summary_file.write_text(summary_content, encoding='utf-8')
            
            logger.info(f"Validation results saved to {validation_dir}")
            
        except Exception as e:
            logger.error(f"Failed to save validation results: {e}")
    
    def _generate_validation_summary(self, validation_results: Dict[str, Any], 
                                   validation_report: ValidationReport) -> str:
        """Generate human-readable validation summary."""
        summary = f"""# System Validation Summary

**Validation Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Overall Score:** {validation_report.overall_score:.2f}/1.00
**Validation Status:** {'✅ PASSED' if validation_report.validation_passed else '❌ FAILED'}

## Components Validated
- Total Components: {validation_report.components_validated}
- Performance Requirements: {'✅' if validation_results.get('performance', {}).get('response_time_compliant', False) else '❌'}
- System Health Check: {'✅' if validation_results.get('health_check', {}).get('overall_health', False) else '❌'}
- Component Status: {'✅' if validation_results.get('component_status', {}).get('health_percentage', 0) > 80 else '❌'}
- Integration Test: {'✅' if validation_results.get('integration', {}).get('passed', False) else '❌'}

## Performance Metrics
"""
        
        # Add performance details
        perf_data = validation_results.get('performance', {}).get('detailed_results', {})
        if perf_data:
            summary += f"""
- Average Response Time: {perf_data.get('average_response_time_ms', 0):.2f}ms
- Average Memory Usage: {perf_data.get('average_memory_usage_mb', 0):.2f}MB
- Curriculum Alignment: {perf_data.get('average_curriculum_score', 0):.2f}
"""
        
        # Add health check details
        health_data = validation_results.get('health_check', {})
        if health_data:
            summary += f"""
## System Health
- Overall Health: {'✅ Healthy' if health_data.get('overall_health', False) else '❌ Issues Found'}
- Component Status: {validation_results.get('component_status', {}).get('healthy_components', 0)}/{validation_results.get('component_status', {}).get('total_components', 0)} components healthy
"""
        
        # Add issues and recommendations
        if validation_report.issues_found:
            summary += "\n## Issues Found\n"
            for issue in validation_report.issues_found:
                summary += f"- ❌ {issue}\n"
        
        if validation_report.recommendations:
            summary += "\n## Recommendations\n"
            for rec in validation_report.recommendations:
                summary += f"- 💡 {rec}\n"
        
        summary += f"""
## Next Steps
{'✅ System is ready for production deployment' if validation_report.validation_passed else '⚠️ Address issues before production deployment'}

---
*Generated by OpenClass Nexus AI Optimization System*
"""
        
        return summary