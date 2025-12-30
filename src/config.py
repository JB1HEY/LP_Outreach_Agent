"""
Configuration management for LP Outreach Agent
Loads environment variables and manages user preferences.
"""
import os
import sys
from dataclasses import dataclass, field
from typing import List, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class InvestmentCriteria:
    """Defines the investment criteria for LP search"""
    # Dynamic Toggles
    use_ebitda: bool = True
    use_revenue: bool = True
    use_industries: bool = True
    use_preferences: bool = True
    
    # Values
    ebitda_range: Tuple[float, float] = (1, 5)  # in millions
    revenue_range: Tuple[float, float] = (20, 150)  # in millions
    industries: List[str] = field(default_factory=list)
    company_targets: List[str] = field(default_factory=list)
    preferences: List[str] = field(default_factory=lambda: ["emerging_managers", "special_situations"])

@dataclass
class SearchConfig:
    """Configuration for LP discovery searches"""
    gemini_api_key: str
    max_results_per_search: int = 20
    search_depth: str = "comprehensive"
    categories: List[str] = field(default_factory=lambda: [
        "GP Investor",
        "Fund Investor", 
        "HNW Individual",
        "Family Office"
    ])

def load_config() -> Tuple[SearchConfig, InvestmentCriteria]:
    """Load configuration from environment and defaults"""
    
    # Get API Key from environment
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ CRITICAL ERROR: API Key not found!")
        print("Please create a .env file in the project root with the following content:")
        print("GEMINI_API_KEY=your_api_key_here")
        sys.exit(1)
        
    search_config = SearchConfig(gemini_api_key=api_key)
    
    # Default criteria - could be extended to load from a JSON preference file if desired
    # For now, we keep the default hardcoded or modified via code as requested
    criteria = InvestmentCriteria(
         industries=["SaaS", "Fintech", "Healthcare IT"],
         company_targets=["B2B Software", "Enterprise Solutions"]
    )
    
    return search_config, criteria
