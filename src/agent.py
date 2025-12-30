"""
Core LP Database Management Logic
"""
import pandas as pd
from datetime import datetime
import os

class LPOutreachAgent:
    def __init__(self, data_file='lp_database.csv'):
        # Ensure data file is stored in root directory even if run from src
        if not os.path.isabs(data_file):
            # Assuming CWD is root of project
            self.data_file = data_file
        else:
            self.data_file = data_file
            
        try:
            self.lps = pd.read_csv(self.data_file)
            
            # Ensure all required columns exist (schema migration)
            required_columns = [
                'LP_Name', 'Firm', 'Email', 'Interests', 'Status',
                'Last_Contact', 'Next_Action', 'Notes',
                'LP_Category', 'EBITDA_Range', 'Revenue_Range', 
                'Investment_Preferences', 'Industries', 'Deal_History',
                'Discovery_Date', 'Confidence_Score'
            ]
            
            for col in required_columns:
                if col not in self.lps.columns:
                    self.lps[col] = ''
            
        except FileNotFoundError:
            # Initialize empty DataFrame if file doesn't exist
            self.lps = pd.DataFrame(columns=[
                'LP_Name', 'Firm', 'Email', 'Interests', 'Status',
                'Last_Contact', 'Next_Action', 'Notes',
                # New fields for automated discovery
                'LP_Category', 'EBITDA_Range', 'Revenue_Range', 
                'Investment_Preferences', 'Industries', 'Deal_History',
                'Discovery_Date', 'Confidence_Score'
            ])
            self.save_data()

    def save_data(self):
        self.lps.to_csv(self.data_file, index=False)

    def add_lp(self, name, firm, email, interests, lp_category='', ebitda_range='', 
               revenue_range='', investment_preferences='', industries='', deal_history='',
               discovery_date='', confidence_score=0):
        new_lp = {
            'LP_Name': name,
            'Firm': firm,
            'Email': email,
            'Interests': interests,  # Store as string for pandas compatibility
            'Status': 'Prospect',
            'Last_Contact': None,
            'Next_Action': 'Initial Outreach',
            'Notes': '',
            # New fields
            'LP_Category': lp_category,
            'EBITDA_Range': ebitda_range,
            'Revenue_Range': revenue_range,
            'Investment_Preferences': investment_preferences,
            'Industries': industries,
            'Deal_History': deal_history,
            'Discovery_Date': discovery_date,
            'Confidence_Score': confidence_score
        }
        self.lps = pd.concat([self.lps, pd.DataFrame([new_lp])], ignore_index=True)
        self.save_data()
        print(f"Added LP: {name} from {firm}")

    def generate_outreach_message(self, lp_name, fund_name, value_prop, intro_source=None):
        # Check if LP exists
        lp_match = self.lps[self.lps['LP_Name'] == lp_name]
        if lp_match.empty:
            return f"Error: LP '{lp_name}' not found in database."
        
        lp = lp_match.iloc[0]
        interests = lp['Interests']
        
        message = f"Subject: Exploring Opportunities in {fund_name}\n\n"
        message += f"Dear {lp_name},\n\n"
        if intro_source:
            message += f"I was introduced to you by {intro_source}, who mentioned your interest in {interests}.\n\n"
        else:
            message += f"I came across your work at {lp['Firm']} and noted your focus on {interests}.\n\n"
        message += f"Our fund, {fund_name}, specializes in {value_prop}. We'd love to discuss how this aligns with your portfolio.\n\n"
        message += "Best regards,\nYour Name\nYour Fund"
        return message

    def log_interaction(self, lp_name, interaction_type, notes=''):
        # Check if LP exists
        lp_match = self.lps[self.lps['LP_Name'] == lp_name]
        if lp_match.empty:
            print(f"Error: LP '{lp_name}' not found in database.")
            return
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        idx = lp_match.index[0]
        self.lps.at[idx, 'Last_Contact'] = now
        current_notes = self.lps.at[idx, 'Notes']
        if pd.isna(current_notes):
            current_notes = ''
        self.lps.at[idx, 'Notes'] = current_notes + f"\n{now}: {interaction_type} - {notes}"
        
        # Update status and next action based on interaction
        if interaction_type == 'Initial Outreach':
            self.lps.at[idx, 'Status'] = 'Contacted'
            self.lps.at[idx, 'Next_Action'] = 'Follow-up in 1 week'
        elif interaction_type == 'Follow-up':
            self.lps.at[idx, 'Status'] = 'Engaged'
            self.lps.at[idx, 'Next_Action'] = 'Schedule Meeting'
        elif interaction_type == 'Meeting':
            self.lps.at[idx, 'Status'] = 'In Discussion'
            self.lps.at[idx, 'Next_Action'] = 'Send Deck'
        self.save_data()
        print(f"Logged interaction for {lp_name}: {interaction_type}")

    def get_summary(self):
        summary = self.lps.groupby('Status').size().reset_index(name='Count')
        return summary

    def recommend_actions(self):
        actions = []
        for _, lp in self.lps.iterrows():
            if lp['Next_Action'] and pd.notna(lp['Next_Action']):
                actions.append(f"{lp['LP_Name']}: {lp['Next_Action']}")
        return actions
    
    def import_discovered_lps(self, discovered_lps):
        """Batch import LPs from discovery engine"""
        
        imported_count = 0
        for lp in discovered_lps:
            # Check if LP already exists
            existing = self.lps[self.lps['Firm'] == lp.get('Firm', '')]
            if existing.empty:
                # Add discovery date if not present
                if not lp.get('Discovery_Date'):
                    lp['Discovery_Date'] = datetime.now().strftime('%Y-%m-%d')
                
                # Create new LP entry
                new_lp = pd.DataFrame([lp])
                self.lps = pd.concat([self.lps, new_lp], ignore_index=True)
                imported_count += 1
        
        self.save_data()
        print(f"Imported {imported_count} new LPs (skipped {len(discovered_lps) - imported_count} duplicates)")
        return imported_count
    
    def filter_by_criteria(self, category=None, min_confidence=0, industries=None, status=None):
        """Advanced filtering by multiple criteria"""
        filtered = self.lps.copy()
        
        if category:
            filtered = filtered[filtered['LP_Category'] == category]
        
        if min_confidence > 0:
            filtered = filtered[pd.to_numeric(filtered['Confidence_Score'], errors='coerce') >= min_confidence]
        
        if industries:
            # Filter by industries (partial match)
            industry_mask = filtered['Industries'].str.contains('|'.join(industries), case=False, na=False)
            filtered = filtered[industry_mask]
        
        if status:
            filtered = filtered[filtered['Status'] == status]
        
        return filtered
    
    def get_lps_by_category(self):
        """Get LPs grouped by category"""
        if 'LP_Category' not in self.lps.columns or self.lps['LP_Category'].isna().all():
            return {}
        
        categories = {}
        for category in self.lps['LP_Category'].unique():
            if pd.notna(category) and category:
                categories[category] = self.lps[self.lps['LP_Category'] == category]
        
        return categories
    
    def generate_daily_target_list(self, target_count=10, prioritize_category=None):
        """Generate prioritized daily target list"""
        # Filter prospects and contacted LPs
        targets = self.lps[self.lps['Status'].isin(['Prospect', 'Contacted'])].copy()
        
        if targets.empty:
            return pd.DataFrame()
        
        # Calculate priority score
        targets['Priority_Score'] = 0
        
        # Higher confidence = higher priority
        targets['Priority_Score'] += pd.to_numeric(targets['Confidence_Score'], errors='coerce').fillna(0) * 0.5
        
        # Prospects get higher priority than contacted
        targets.loc[targets['Status'] == 'Prospect', 'Priority_Score'] += 30
        
        # Prioritize specific category if requested
        if prioritize_category:
            targets.loc[targets['LP_Category'] == prioritize_category, 'Priority_Score'] += 20
        
        # Sort by priority and return top N
        targets = targets.sort_values('Priority_Score', ascending=False)
        return targets.head(target_count)
