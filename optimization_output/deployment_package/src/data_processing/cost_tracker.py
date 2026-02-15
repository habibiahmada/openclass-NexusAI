"""Cost Tracking Module

This module tracks AWS costs during ETL pipeline processing,
including Bedrock token usage and S3 data transfer.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class CostEntry:
    """Single cost tracking entry for a pipeline run."""
    timestamp: str
    tokens_processed: int
    bedrock_cost: float
    s3_data_mb: float
    s3_cost: float
    total_cost: float
    files_processed: int
    chunks_processed: int


@dataclass
class CostLog:
    """Complete cost log with all pipeline runs."""
    pipeline_runs: List[CostEntry] = field(default_factory=list)
    total_cost_to_date: float = 0.0
    budget_limit: float = 1.0  # $1.00 default budget
    budget_remaining: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'pipeline_runs': [asdict(entry) for entry in self.pipeline_runs],
            'total_cost_to_date': self.total_cost_to_date,
            'budget_limit': self.budget_limit,
            'budget_remaining': self.budget_remaining
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CostLog':
        """Create CostLog from dictionary."""
        pipeline_runs = [
            CostEntry(**entry) for entry in data.get('pipeline_runs', [])
        ]
        return cls(
            pipeline_runs=pipeline_runs,
            total_cost_to_date=data.get('total_cost_to_date', 0.0),
            budget_limit=data.get('budget_limit', 1.0),
            budget_remaining=data.get('budget_remaining', 1.0)
        )


class CostTracker:
    """Tracks and monitors AWS costs during pipeline execution."""
    
    # AWS Pricing (as of 2026)
    BEDROCK_COST_PER_1K_TOKENS = 0.0001  # Titan Text Embeddings v2
    S3_COST_PER_GB = 0.023  # Standard storage
    BUDGET_ALERT_THRESHOLD = 0.80  # 80% of budget
    
    def __init__(self, log_path: str = "data/processed/metadata/cost_log.json", budget_limit: float = 1.0):
        """Initialize cost tracker.
        
        Args:
            log_path: Path to cost log JSON file
            budget_limit: Budget limit in USD (default $1.00)
        """
        self.log_path = Path(log_path)
        self.budget_limit = budget_limit
        self.cost_log = self._load_cost_log()
        
        # Current run tracking
        self.current_tokens = 0
        self.current_s3_mb = 0.0
        
        logger.info(f"Initialized CostTracker with budget: ${budget_limit:.2f}")
        logger.info(f"Current total cost: ${self.cost_log.total_cost_to_date:.4f}")
        logger.info(f"Budget remaining: ${self.cost_log.budget_remaining:.4f}")
    
    def _load_cost_log(self) -> CostLog:
        """Load existing cost log or create new one.
        
        Returns:
            CostLog object
        """
        if self.log_path.exists():
            try:
                with open(self.log_path, 'r') as f:
                    data = json.load(f)
                    cost_log = CostLog.from_dict(data)
                    # Update budget limit if changed
                    cost_log.budget_limit = self.budget_limit
                    cost_log.budget_remaining = self.budget_limit - cost_log.total_cost_to_date
                    logger.info(f"Loaded existing cost log from {self.log_path}")
                    return cost_log
            except Exception as e:
                logger.warning(f"Failed to load cost log: {e}. Creating new log.")
                return CostLog(budget_limit=self.budget_limit, budget_remaining=self.budget_limit)
        else:
            logger.info("No existing cost log found. Creating new log.")
            return CostLog(budget_limit=self.budget_limit, budget_remaining=self.budget_limit)
    
    def _save_cost_log(self):
        """Save cost log to disk."""
        try:
            # Ensure directory exists
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to JSON
            with open(self.log_path, 'w') as f:
                json.dump(self.cost_log.to_dict(), f, indent=2)
            
            logger.info(f"Saved cost log to {self.log_path}")
        except Exception as e:
            logger.error(f"Failed to save cost log: {e}")
    
    def track_bedrock_tokens(self, tokens: int):
        """Track Bedrock token usage.
        
        Args:
            tokens: Number of tokens processed
        """
        self.current_tokens += tokens
        logger.debug(f"Tracked {tokens} Bedrock tokens (total: {self.current_tokens})")
    
    def track_s3_transfer(self, size_mb: float):
        """Track S3 data transfer.
        
        Args:
            size_mb: Data size in megabytes
        """
        self.current_s3_mb += size_mb
        logger.debug(f"Tracked {size_mb:.2f} MB S3 transfer (total: {self.current_s3_mb:.2f} MB)")
    
    def calculate_bedrock_cost(self, tokens: Optional[int] = None) -> float:
        """Calculate Bedrock cost based on token usage.
        
        Args:
            tokens: Number of tokens (uses current_tokens if None)
            
        Returns:
            Cost in USD
        """
        tokens_to_use = tokens if tokens is not None else self.current_tokens
        return (tokens_to_use / 1000) * self.BEDROCK_COST_PER_1K_TOKENS
    
    def calculate_s3_cost(self, size_mb: Optional[float] = None) -> float:
        """Calculate S3 cost based on data transfer.
        
        Args:
            size_mb: Data size in MB (uses current_s3_mb if None)
            
        Returns:
            Cost in USD
        """
        size_to_use = size_mb if size_mb is not None else self.current_s3_mb
        size_gb = size_to_use / 1024  # Convert MB to GB
        return size_gb * self.S3_COST_PER_GB
    
    def calculate_total_cost(self) -> float:
        """Calculate total cost for current run.
        
        Returns:
            Total cost in USD
        """
        bedrock_cost = self.calculate_bedrock_cost()
        s3_cost = self.calculate_s3_cost()
        return bedrock_cost + s3_cost
    
    def record_pipeline_run(self, files_processed: int, chunks_processed: int) -> CostEntry:
        """Record a completed pipeline run.
        
        Args:
            files_processed: Number of files processed
            chunks_processed: Number of chunks processed
            
        Returns:
            CostEntry for this run
        """
        bedrock_cost = self.calculate_bedrock_cost()
        s3_cost = self.calculate_s3_cost()
        total_cost = bedrock_cost + s3_cost
        
        entry = CostEntry(
            timestamp=datetime.now().isoformat(),
            tokens_processed=self.current_tokens,
            bedrock_cost=bedrock_cost,
            s3_data_mb=self.current_s3_mb,
            s3_cost=s3_cost,
            total_cost=total_cost,
            files_processed=files_processed,
            chunks_processed=chunks_processed
        )
        
        # Add to log
        self.cost_log.pipeline_runs.append(entry)
        self.cost_log.total_cost_to_date += total_cost
        self.cost_log.budget_remaining = self.cost_log.budget_limit - self.cost_log.total_cost_to_date
        
        # Save to disk
        self._save_cost_log()
        
        # Check budget alert
        self._check_budget_alert()
        
        # Reset current run tracking
        self.current_tokens = 0
        self.current_s3_mb = 0.0
        
        logger.info(f"Recorded pipeline run: ${total_cost:.4f} (Bedrock: ${bedrock_cost:.4f}, S3: ${s3_cost:.4f})")
        
        return entry
    
    def _check_budget_alert(self):
        """Check if budget threshold is exceeded and send alert."""
        budget_used_percentage = self.cost_log.total_cost_to_date / self.cost_log.budget_limit
        
        if budget_used_percentage >= self.BUDGET_ALERT_THRESHOLD:
            alert_message = (
                f"⚠️  BUDGET ALERT: {budget_used_percentage * 100:.1f}% of budget used!\n"
                f"   Total cost: ${self.cost_log.total_cost_to_date:.4f}\n"
                f"   Budget limit: ${self.cost_log.budget_limit:.2f}\n"
                f"   Remaining: ${self.cost_log.budget_remaining:.4f}"
            )
            logger.warning(alert_message)
            print("\n" + "=" * 60)
            print(alert_message)
            print("=" * 60 + "\n")
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get summary of costs.
        
        Returns:
            Dictionary with cost summary
        """
        return {
            'current_run': {
                'tokens': self.current_tokens,
                'bedrock_cost': self.calculate_bedrock_cost(),
                's3_mb': self.current_s3_mb,
                's3_cost': self.calculate_s3_cost(),
                'total_cost': self.calculate_total_cost()
            },
            'total_to_date': self.cost_log.total_cost_to_date,
            'budget_limit': self.cost_log.budget_limit,
            'budget_remaining': self.cost_log.budget_remaining,
            'budget_used_percentage': (self.cost_log.total_cost_to_date / self.cost_log.budget_limit) * 100,
            'total_runs': len(self.cost_log.pipeline_runs)
        }
    
    def print_cost_summary(self):
        """Print formatted cost summary."""
        summary = self.get_cost_summary()
        
        print("\n" + "=" * 60)
        print("COST SUMMARY")
        print("=" * 60)
        print(f"Current Run:")
        print(f"  Bedrock tokens: {summary['current_run']['tokens']:,}")
        print(f"  Bedrock cost: ${summary['current_run']['bedrock_cost']:.4f}")
        print(f"  S3 transfer: {summary['current_run']['s3_mb']:.2f} MB")
        print(f"  S3 cost: ${summary['current_run']['s3_cost']:.4f}")
        print(f"  Total: ${summary['current_run']['total_cost']:.4f}")
        print(f"\nCumulative:")
        print(f"  Total cost to date: ${summary['total_to_date']:.4f}")
        print(f"  Budget limit: ${summary['budget_limit']:.2f}")
        print(f"  Budget remaining: ${summary['budget_remaining']:.4f}")
        print(f"  Budget used: {summary['budget_used_percentage']:.1f}%")
        print(f"  Total pipeline runs: {summary['total_runs']}")
        print("=" * 60 + "\n")
