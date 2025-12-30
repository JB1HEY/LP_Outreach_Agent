"""
Main Entry Point for LP Outreach Agent
"""
import sys
from datetime import datetime
import pandas as pd
from src.discovery import LPDiscoveryEngine
from src.agent import LPOutreachAgent
from src.targets import DailyTargetGenerator
from src.config import load_config, InvestmentCriteria

def main():
    """Main workflow for LP discovery and daily target generation"""
    
    print("="*80)
    print("LP OUTREACH AGENT - AUTOMATED DISCOVERY")
    print("="*80)
    print()
    
    # Step 1: Load configuration
    print("Step 1: Loading configuration...")
    search_config, criteria = load_config()
    print("✓ Configuration loaded from .env and defaults")
    print(f"  API Key status: {'Found' if search_config.gemini_api_key else 'Missing'}")
    
    print(f"  Industries: {', '.join(criteria.industries) if criteria.industries else 'All'}")
    print(f"  EBITDA Range: ${criteria.ebitda_range[0]}M - ${criteria.ebitda_range[1]}M")
    print(f"  Revenue Range: ${criteria.revenue_range[0]}M - ${criteria.revenue_range[1]}M")
    print(f"  Preferences: {', '.join(criteria.preferences)}")
    print()
    
    # Step 2: Initialize discovery engine
    print("Step 2: Initializing discovery engine...")
    try:
        engine = LPDiscoveryEngine(search_config.gemini_api_key)
        print("✓ Gemini API initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Gemini API: {e}")
        return
    print()
    
    # Step 3: Run LP discovery
    print("Step 3: Discovering LPs...")
    print(f"  Search depth: {search_config.search_depth}")
    print(f"  Max results per search: {search_config.max_results_per_search}")
    print()
    
    # Execute Search
    discovered_lps = engine.search_lps(criteria, search_config)
    
    if not discovered_lps:
        print("⚠ No LPs discovered. Try adjusting your search criteria in config.")
        # Proceed anyway to show daily targets from existing db if any
    else:
        print()
        print(f"✓ Discovered {len(discovered_lps)} unique LPs")
        
        # Show breakdown by category
        categories = {}
        for lp in discovered_lps:
            cat = lp.get('LP_Category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\nBreakdown by category:")
        for cat, count in categories.items():
            print(f"  - {cat}: {count}")
        print()
    
    # Step 4: Import to agent database
    print("Step 4: Importing LPs to database...")
    agent = LPOutreachAgent()
    if discovered_lps:
        imported_count = agent.import_discovered_lps(discovered_lps)
        print(f"✓ Imported {imported_count} new LPs")
    else:
        print("✓ Database loaded")
    print()
    
    # Step 5: Generate daily target list
    print("Step 5: Generating daily target list...")
    generator = DailyTargetGenerator(agent)
    
    targets = generator.generate_targets(
        target_count=10,
        min_confidence=40,  # Lower threshold to include more results
        industries=criteria.industries if criteria.industries else None
    )
    
    if targets.empty:
        print("⚠ No targets meet the criteria. Try lowering min_confidence or adjusting filters.")
        return
    
    print(f"✓ Generated {len(targets)} daily targets")
    print()
    
    # Step 6: Export results
    print("Step 6: Exporting results...")
    
    # Export CSV
    csv_file = generator.export_to_csv(targets)
    
    # Create and save report
    report = generator.create_summary_report(targets)
    report_file = f"daily_targets_report_{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"✓ Exported to:")
    print(f"  - {csv_file}")
    print(f"  - {report_file}")
    print()
    
    # Step 7: Display summary
    print("="*80)
    print("DAILY TARGET SUMMARY")
    print("="*80)
    print()
    
    print(f"Top 5 Priority Targets:")
    print()
    
    for i, (_, lp) in enumerate(targets.head(5).iterrows(), 1):
        print(f"{i}. {lp['LP_Name']}")
        print(f"   Firm: {lp['Firm']}")
        print(f"   Category: {lp.get('LP_Category', 'Unknown')}")
        print(f"   Confidence: {lp.get('Confidence_Score', 0)}%")
        if pd.notna(lp.get('Email')):
            print(f"   Contact: {lp['Email']}")
        print()
    
    print("="*80)
    print(f"✓ Discovery complete! Review {report_file} for full details.")
    print("="*80)

if __name__ == "__main__":
    main()
