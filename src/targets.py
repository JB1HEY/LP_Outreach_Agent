"""
Daily Target List Generator for LP Outreach
Creates prioritized lists of LPs for daily outreach activities
"""
import pandas as pd
from datetime import datetime
from typing import Optional

class DailyTargetGenerator:
    """Generates daily target lists from LP database"""
    
    def __init__(self, agent):
        """Initialize with LPOutreachAgent instance"""
        self.agent = agent
    
    def generate_targets(self, target_count=10, prioritize_category=None, 
                        min_confidence=50, industries=None):
        """
        Generate daily target list based on priority scoring
        
        Args:
            target_count: Number of LPs to include in daily list
            prioritize_category: Optional category to prioritize (GP Investor, Fund Investor, etc.)
            min_confidence: Minimum confidence score (0-100)
            industries: Optional list of industries to filter by
        
        Returns:
            DataFrame with prioritized LP targets
        """
        # Get all prospects and contacted LPs
        targets = self.agent.lps[
            self.agent.lps['Status'].isin(['Prospect', 'Contacted'])
        ].copy()
        
        if targets.empty:
            print("No prospects or contacted LPs available for targeting")
            return pd.DataFrame()
        
        # Apply filters
        if min_confidence > 0:
            targets = targets[
                pd.to_numeric(targets['Confidence_Score'], errors='coerce').fillna(0) >= min_confidence
            ]
        
        if industries:
            industry_mask = targets['Industries'].str.contains(
                '|'.join(industries), case=False, na=False
            )
            targets = targets[industry_mask]
        
        if targets.empty:
            print("No LPs match the specified criteria")
            return pd.DataFrame()
        
        # Calculate priority score
        targets = self._calculate_priority_scores(targets, prioritize_category)
        
        # Ensure category diversity in top results
        targets = self._balance_categories(targets, target_count)
        
        # Sort by priority and return top N
        targets = targets.sort_values('Priority_Score', ascending=False).head(target_count)
        
        return targets
    
    def _calculate_priority_scores(self, targets, prioritize_category=None):
        """Calculate priority scores for each LP"""
        targets['Priority_Score'] = 0.0
        
        # 1. Confidence score (0-50 points)
        confidence = pd.to_numeric(targets['Confidence_Score'], errors='coerce').fillna(0)
        targets['Priority_Score'] += confidence * 0.5
        
        # 2. Status priority (30 points for Prospect, 15 for Contacted)
        targets.loc[targets['Status'] == 'Prospect', 'Priority_Score'] += 30
        targets.loc[targets['Status'] == 'Contacted', 'Priority_Score'] += 15
        
        # 3. Category priority (20 points if matches prioritize_category)
        if prioritize_category:
            targets.loc[targets['LP_Category'] == prioritize_category, 'Priority_Score'] += 20
        
        # 4. Recency bonus (10 points for recently discovered)
        if 'Discovery_Date' in targets.columns:
            targets['Discovery_Date'] = pd.to_datetime(targets['Discovery_Date'], errors='coerce')
            days_since_discovery = (datetime.now() - targets['Discovery_Date']).dt.days
            # More recent = higher score
            recency_score = (30 - days_since_discovery).clip(lower=0, upper=10)
            targets['Priority_Score'] += recency_score
        
        # 5. Deal history bonus (10 points if has notable deals)
        has_deals = targets['Deal_History'].notna() & (targets['Deal_History'] != '')
        targets.loc[has_deals, 'Priority_Score'] += 10
        
        return targets
    
    def _balance_categories(self, targets, target_count):
        """Ensure category diversity in results"""
        if 'LP_Category' not in targets.columns:
            return targets
        
        categories = targets['LP_Category'].unique()
        if len(categories) <= 1:
            return targets
        
        # Aim for balanced representation
        per_category = max(2, target_count // len(categories))
        
        balanced = []
        for category in categories:
            category_lps = targets[targets['LP_Category'] == category].head(per_category)
            balanced.append(category_lps)
        
        balanced_df = pd.concat(balanced, ignore_index=True)
        
        # If we don't have enough, fill with highest priority remaining
        if len(balanced_df) < target_count:
            remaining = targets[~targets.index.isin(balanced_df.index)]
            additional = remaining.nlargest(target_count - len(balanced_df), 'Priority_Score')
            balanced_df = pd.concat([balanced_df, additional], ignore_index=True)
        
        return balanced_df
    
    def export_to_csv(self, targets, filename=None):
        """Export daily target list to CSV"""
        if filename is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f'daily_targets_{date_str}.csv'
        
        # Select relevant columns for export
        export_cols = [
            'LP_Name', 'Firm', 'Email', 'LP_Category', 'Interests',
            'Industries', 'EBITDA_Range', 'Revenue_Range', 
            'Investment_Preferences', 'Deal_History', 'Confidence_Score',
            'Status', 'Next_Action', 'Priority_Score'
        ]
        
        # Only include columns that exist
        available_cols = [col for col in export_cols if col in targets.columns]
        export_df = targets[available_cols]
        
        export_df.to_csv(filename, index=False)
        print(f"Daily target list exported to {filename}")
        return filename
    
    def create_summary_report(self, targets):
        """Create markdown summary report of daily targets"""
        if targets.empty:
            return "No targets available for today."
        
        report = f"# Daily LP Outreach Targets - {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        # Summary statistics
        report += "## Summary\n\n"
        report += f"- **Total Targets**: {len(targets)}\n"
        
        if 'LP_Category' in targets.columns:
            category_counts = targets['LP_Category'].value_counts()
            report += f"- **By Category**:\n"
            for category, count in category_counts.items():
                report += f"  - {category}: {count}\n"
        
        if 'Confidence_Score' in targets.columns:
            avg_confidence = targets['Confidence_Score'].mean()
            report += f"- **Average Confidence Score**: {avg_confidence:.1f}%\n"
        
        report += "\n---\n\n"
        
        # Top targets by category
        report += "## Recommended Outreach Order\n\n"
        
        for i, (_, lp) in enumerate(targets.iterrows(), 1):
            report += f"### {i}. {lp['LP_Name']}\n\n"
            report += f"- **Firm**: {lp['Firm']}\n"
            if 'LP_Category' in lp and pd.notna(lp['LP_Category']):
                report += f"- **Category**: {lp['LP_Category']}\n"
            if 'Email' in lp and pd.notna(lp['Email']):
                report += f"- **Contact**: {lp['Email']}\n"
            if 'Interests' in lp and pd.notna(lp['Interests']):
                report += f"- **Focus**: {lp['Interests']}\n"
            if 'Deal_History' in lp and pd.notna(lp['Deal_History']):
                deal_history = str(lp['Deal_History'])[:150]
                report += f"- **Notable Deals**: {deal_history}\n"
            if 'Investment_Preferences' in lp and pd.notna(lp['Investment_Preferences']):
                report += f"- **Preferences**: {lp['Investment_Preferences']}\n"
            if 'Confidence_Score' in lp and pd.notna(lp['Confidence_Score']):
                report += f"- **Confidence**: {lp['Confidence_Score']}%\n"
            
            report += f"\n**Key Talking Points**:\n"
            if 'Industries' in lp and pd.notna(lp['Industries']):
                report += f"- Alignment with {lp['Industries']} focus\n"
            if 'EBITDA_Range' in lp and pd.notna(lp['EBITDA_Range']):
                report += f"- Target EBITDA range: {lp['EBITDA_Range']}\n"
            if 'Revenue_Range' in lp and pd.notna(lp['Revenue_Range']):
                report += f"- Target revenue range: {lp['Revenue_Range']}\n"
            
            report += "\n---\n\n"
        
        return report
