"""
Final Validation Executor

This module executes the comprehensive system validation for subtask 10.1,
including performance requirements, health checks, and production readiness assessment.
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from .system_validator import SystemValidator
from .deployment_packager import DeploymentPackager
from .final_report_generator import FinalReportGenerator
from .models import ValidationReport, DeploymentPackage
from .config import OptimizationConfig

logger = logging.getLogger(__name__)


class FinalValidationExecutor:
    """Executes final validation and production package creation."""
    
    def __init__(self, config: OptimizationConfig = None):
        """Initialize the final validation executor."""
        self.config = config or OptimizationConfig()
        self.output_dir = self.config.optimization_output_dir
        
        # Initialize components
        self.system_validator = SystemValidator(self.config)
        self.deployment_packager = DeploymentPackager(self.config)
        self.report_generator = FinalReportGenerator(self.config)
        
        logger.info("Final validation executor initialized")
    
    def execute_subtask_10_1(self) -> ValidationReport:
        """Execute subtask 10.1: Comprehensive system validation."""
        logger.info("Executing subtask 10.1: Comprehensive system validation")
        
        try:
            # Run comprehensive system validation
            validation_report = self.system_validator.execute_comprehensive_validation()
            
            # Log results
            logger.info(f"System validation completed with score: {validation_report.overall_score:.2f}")
            logger.info(f"Validation passed: {validation_report.validation_passed}")
            
            if validation_report.issues_found:
                logger.warning(f"Issues found: {len(validation_report.issues_found)}")
                for issue in validation_report.issues_found:
                    logger.warning(f"  - {issue}")
            
            if validation_report.recommendations:
                logger.info(f"Recommendations: {len(validation_report.recommendations)}")
                for rec in validation_report.recommendations:
                    logger.info(f"  - {rec}")
            
            return validation_report
            
        except Exception as e:
            logger.error(f"Subtask 10.1 failed: {e}")
            raise
    
    def execute_subtask_10_2(self) -> Dict[str, DeploymentPackage]:
        """Execute subtask 10.2: Create final deployment packages."""
        logger.info("Executing subtask 10.2: Create final deployment packages")
        
        try:
            # Create deployment packages
            deployment_packages = self.deployment_packager.create_final_deployment_packages()
            
            # Generate deployment summary
            summary = self.deployment_packager.generate_deployment_summary(deployment_packages)
            
            # Save deployment summary
            summary_file = self.output_dir / "DEPLOYMENT_SUMMARY.md"
            summary_file.write_text(summary, encoding='utf-8')
            
            logger.info(f"Created {len(deployment_packages)} deployment packages")
            for package_name, package in deployment_packages.items():
                logger.info(f"  - {package_name}: {package.package_size_mb:.2f} MB")
            
            return deployment_packages
            
        except Exception as e:
            logger.error(f"Subtask 10.2 failed: {e}")
            raise
    
    def execute_subtask_10_3(self, validation_report: ValidationReport, 
                           deployment_packages: Dict[str, DeploymentPackage]) -> str:
        """Execute subtask 10.3: Generate final optimization report."""
        logger.info("Executing subtask 10.3: Generate final optimization report")
        
        try:
            # Generate comprehensive final report
            report_path = self.report_generator.generate_final_optimization_report(
                validation_report, deployment_packages
            )
            
            # Generate executive summary
            executive_summary = self.report_generator.generate_executive_summary(validation_report)
            
            logger.info(f"Final optimization report generated: {report_path}")
            logger.info("Executive summary generated for stakeholders")
            
            return report_path
            
        except Exception as e:
            logger.error(f"Subtask 10.3 failed: {e}")
            raise
    
    def execute_complete_task_10(self) -> Dict[str, Any]:
        """Execute complete task 10: Final validation and production package creation."""
        logger.info("Executing complete task 10: Final validation and production package creation")
        
        execution_results = {
            "task_10_status": "in_progress",
            "subtasks_completed": [],
            "validation_report": None,
            "deployment_packages": None,
            "final_report_path": None,
            "execution_summary": {}
        }
        
        try:
            # Execute subtask 10.1
            logger.info("Starting subtask 10.1...")
            validation_report = self.execute_subtask_10_1()
            execution_results["validation_report"] = validation_report
            execution_results["subtasks_completed"].append("10.1")
            logger.info("✅ Subtask 10.1 completed successfully")
            
            # Execute subtask 10.2
            logger.info("Starting subtask 10.2...")
            deployment_packages = self.execute_subtask_10_2()
            execution_results["deployment_packages"] = deployment_packages
            execution_results["subtasks_completed"].append("10.2")
            logger.info("✅ Subtask 10.2 completed successfully")
            
            # Execute subtask 10.3
            logger.info("Starting subtask 10.3...")
            final_report_path = self.execute_subtask_10_3(validation_report, deployment_packages)
            execution_results["final_report_path"] = final_report_path
            execution_results["subtasks_completed"].append("10.3")
            logger.info("✅ Subtask 10.3 completed successfully")
            
            # Update task status
            execution_results["task_10_status"] = "completed"
            
            # Generate execution summary
            execution_results["execution_summary"] = {
                "total_subtasks": 3,
                "completed_subtasks": len(execution_results["subtasks_completed"]),
                "validation_score": validation_report.overall_score,
                "validation_passed": validation_report.validation_passed,
                "deployment_packages_created": len(deployment_packages),
                "issues_found": len(validation_report.issues_found),
                "recommendations_provided": len(validation_report.recommendations),
                "execution_time": datetime.now().isoformat()
            }
            
            # Save execution results
            self._save_execution_results(execution_results)
            
            logger.info("🎉 Task 10 completed successfully!")
            logger.info(f"Validation Score: {validation_report.overall_score:.1%}")
            logger.info(f"Deployment Packages: {len(deployment_packages)}")
            logger.info(f"Final Report: {final_report_path}")
            
            return execution_results
            
        except Exception as e:
            execution_results["task_10_status"] = "failed"
            execution_results["error"] = str(e)
            logger.error(f"Task 10 execution failed: {e}")
            raise
    
    def _save_execution_results(self, execution_results: Dict[str, Any]):
        """Save execution results to file."""
        try:
            results_file = self.output_dir / "task_10_execution_results.json"
            
            # Convert complex objects to dictionaries for JSON serialization
            serializable_results = execution_results.copy()
            
            if execution_results["validation_report"]:
                serializable_results["validation_report"] = execution_results["validation_report"].to_dict()
            
            if execution_results["deployment_packages"]:
                serializable_results["deployment_packages"] = {
                    name: package.to_dict() 
                    for name, package in execution_results["deployment_packages"].items()
                }
            
            with open(results_file, 'w') as f:
                json.dump(serializable_results, f, indent=2, default=str)
            
            logger.info(f"Execution results saved to {results_file}")
            
        except Exception as e:
            logger.error(f"Failed to save execution results: {e}")


def main():
    """Main function for executing task 10."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize and execute
        executor = FinalValidationExecutor()
        results = executor.execute_complete_task_10()
        
        print("\n" + "="*60)
        print("TASK 10 EXECUTION COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Validation Score: {results['execution_summary']['validation_score']:.1%}")
        print(f"Validation Passed: {results['execution_summary']['validation_passed']}")
        print(f"Deployment Packages: {results['execution_summary']['deployment_packages_created']}")
        print(f"Issues Found: {results['execution_summary']['issues_found']}")
        print(f"Final Report: {results['final_report_path']}")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Task 10 execution failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)