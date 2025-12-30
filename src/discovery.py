"""
LP Discovery Engine using Gemini API
Automatically discovers and categorizes Limited Partners based on investment criteria
"""
from google import genai
from google.genai import types
from typing import List, Dict, Optional
import json
import re
from .config import SearchConfig, InvestmentCriteria

class LPDiscoveryEngine:
    """Main engine for discovering LPs using Gemini API"""
    
    def __init__(self, api_key: str):
        """Initialize the discovery engine with Gemini API key"""
        # Configure the new google.genai Client
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-2.0-flash'
        
    def search_lps(self, criteria: InvestmentCriteria, config: SearchConfig) -> List[Dict]:
        """
        Execute LP search based on investment criteria
        Returns list of discovered LPs with structured data
        """
        all_lps = []
        
        # Generate search queries based on criteria
        search_queries = self._generate_search_queries(criteria, config)
        
        print(f"Executing {len(search_queries)} search queries...")
        
        for i, query in enumerate(search_queries, 1):
            print(f"\nSearch {i}/{len(search_queries)}: {query['description']}")
            lps = self._execute_search(query['prompt'], query['category'], criteria)
            all_lps.extend(lps)
            print(f"  Found {len(lps)} potential LPs")
        
        # Remove duplicates based on firm name
        unique_lps = self._deduplicate_lps(all_lps)
        print(f"\nTotal unique LPs discovered: {len(unique_lps)}")
        
        return unique_lps
    
    def _generate_search_queries(self, criteria: InvestmentCriteria, config: SearchConfig) -> List[Dict]:
        """Generate targeted search queries based on criteria and categories"""
        queries = []
        
        # Build criteria description dynamically based on toggles
        criteria_desc = "Investment Criteria:\n"
        
        if criteria.use_ebitda:
            criteria_desc += f"- EBITDA Range: ${criteria.ebitda_range[0]}M - ${criteria.ebitda_range[1]}M\n"
            
        if criteria.use_revenue:
            criteria_desc += f"- Revenue Range: ${criteria.revenue_range[0]}M - ${criteria.revenue_range[1]}M\n"
            
        if criteria.use_preferences and criteria.preferences:
            criteria_desc += f"- Preferences: {', '.join(criteria.preferences)}\n"
        
        if criteria.use_industries and criteria.industries:
            criteria_desc += f"- Industries: {', '.join(criteria.industries)}\n"
        
        if criteria.company_targets:
            criteria_desc += f"- Company Targets: {', '.join(criteria.company_targets)}\n"
        
        # Category-specific searches
        for category in config.categories:
            if category == "GP Investor":
                queries.append({
                    'category': category,
                    'description': f'GP investors in target industries',
                    'prompt': f"""Find General Partner (GP) investors and venture capital firms that invest in companies with the following criteria:
{criteria_desc}

Please provide a list of 10-15 GP investors with:
1. Investor/Firm Name
2. Contact person (if available)
3. Email or website
4. Investment focus/industries
5. Notable deals or portfolio companies
6. Investment size preference

Format the response as a JSON array of objects."""
                })
            
            elif category == "Fund Investor":
                queries.append({
                    'category': category,
                    'description': f'Fund investors (LPs in VC/PE funds)',
                    'prompt': f"""Find institutional fund investors (Limited Partners) that invest in venture capital and private equity funds, particularly those interested in:
{criteria_desc}

Please provide a list of 10-15 fund investors with:
1. Investor/Institution Name
2. Contact person (if available)
3. Email or website
4. Investment focus/strategy
5. Fund commitments or portfolio
6. Preferences (emerging managers, special situations, etc.)

Format the response as a JSON array of objects."""
                })
            
            elif category == "HNW Individual":
                queries.append({
                    'category': category,
                    'description': f'High Net Worth individuals',
                    'prompt': f"""Find High Net Worth (HNW) individual investors and angel investors who invest in companies or funds with:
{criteria_desc}

Please provide a list of 10-15 HNW individuals with:
1. Investor Name
2. Background/Company affiliation
3. Contact information or LinkedIn
4. Investment interests
5. Notable investments
6. Investment preferences

Format the response as a JSON array of objects."""
                })
            
            elif category == "Family Office":
                queries.append({
                    'category': category,
                    'description': f'Family offices',
                    'prompt': f"""Find family offices that invest in companies or funds with:
{criteria_desc}

Please provide a list of 10-15 family offices with:
1. Family Office Name
2. Principal family or contact
3. Contact information or website
4. Investment focus/sectors
5. Investment history or portfolio
6. Investment preferences (emerging managers, special situations, etc.)

Format the response as a JSON array of objects."""
                })
        
        # Industry-specific searches if specified and enabled matches
        if criteria.use_industries and criteria.industries and config.search_depth == "comprehensive":
            for industry in criteria.industries[:3]:  # Limit to top 3 industries
                queries.append({
                    'category': 'Mixed',
                    'description': f'Investors focused on {industry}',
                    'prompt': f"""Find investors (GPs, funds, family offices, or HNW individuals) specifically focused on the {industry} industry who invest in companies with:
- EBITDA: ${criteria.ebitda_range[0]}M - ${criteria.ebitda_range[1]}M
- Revenue: ${criteria.revenue_range[0]}M - ${criteria.revenue_range[1]}M

Please provide a list of 10 investors with:
1. Investor Name and Type (GP/Fund/Family Office/HNW)
2. Contact information
3. Investment focus
4. Notable {industry} investments
5. Investment preferences

Format the response as a JSON array of objects."""
                })
        
        return queries
    
    def _execute_search(self, prompt: str, category: str, criteria: InvestmentCriteria) -> List[Dict]:
        """Execute a single search query using Gemini API"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            # Extract and parse JSON from response
            lps = self._parse_gemini_response(response.text, category)
            
            # Validate and enrich LP data
            validated_lps = []
            for lp in lps:
                enriched_lp = self._enrich_lp_data(lp, criteria, category)
                if enriched_lp:
                    validated_lps.append(enriched_lp)
            
            return validated_lps
            
        except Exception as e:
            print(f"  Error executing search: {str(e)}")
            return []
    
    def _parse_gemini_response(self, response_text: str, category: str) -> List[Dict]:
        """Parse Gemini API response and extract LP data"""
        try:
            # Try to find JSON array in the response
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                lps_data = json.loads(json_match.group())
                return lps_data
            else:
                # If no JSON found, try to parse structured text
                return self._parse_structured_text(response_text, category)
        except json.JSONDecodeError:
            # Fallback to text parsing
            return self._parse_structured_text(response_text, category)
    
    def _parse_structured_text(self, text: str, category: str) -> List[Dict]:
        """Parse structured text response when JSON parsing fails"""
        lps = []
        
        # Split by numbered items
        items = re.split(r'\n\d+\.', text)
        
        for item in items[1:]:  # Skip first empty split
            lp = {
                'category': category,
                'raw_text': item.strip()
            }
            
            # Try to extract name (usually first line)
            lines = item.strip().split('\n')
            if lines:
                lp['name'] = lines[0].strip('*- ').split(':')[0].strip()
            
            lps.append(lp)
        
        return lps[:15]  # Limit to 15 results
    
    def _enrich_lp_data(self, lp: Dict, criteria: InvestmentCriteria, category: str) -> Optional[Dict]:
        """Enrich and validate LP data"""
        # Ensure required fields
        if 'name' not in lp and 'Investor Name' in lp:
            lp['name'] = lp['Investor Name']
        elif 'name' not in lp and 'Investor/Firm Name' in lp:
            lp['name'] = lp['Investor/Firm Name']
        elif 'name' not in lp and 'Family Office Name' in lp:
            lp['name'] = lp['Family Office Name']
        
        if 'name' not in lp or not lp['name']:
            return None
        
        # Standardize field names
        enriched = {
            'LP_Name': lp.get('name', lp.get('Investor Name', '')),
            'Firm': lp.get('Investor/Firm Name', lp.get('Family Office Name', lp.get('name', ''))),
            'Email': lp.get('Email or website', lp.get('Contact information', lp.get('email', ''))),
            'Interests': lp.get('Investment focus/industries', lp.get('Investment interests', '')),
            'LP_Category': category if category != 'Mixed' else self.categorize_lp(lp),
            'EBITDA_Range': f"${criteria.ebitda_range[0]}M-${criteria.ebitda_range[1]}M",
            'Revenue_Range': f"${criteria.revenue_range[0]}M-${criteria.revenue_range[1]}M",
            'Investment_Preferences': ', '.join(criteria.preferences),
            'Industries': ', '.join(criteria.industries) if criteria.industries else '',
            'Deal_History': lp.get('Notable deals or portfolio companies', lp.get('Notable investments', '')),
            'Confidence_Score': self._calculate_confidence_score(lp),
            'Status': 'Prospect',
            'Next_Action': 'Initial Outreach',
            'Notes': f"Discovered via automated search. {lp.get('raw_text', '')[:200]}"
        }
        
        return enriched
    
    def categorize_lp(self, lp: Dict) -> str:
        """Categorize LP based on available information"""
        lp_text = str(lp).lower()
        
        if 'family office' in lp_text:
            return 'Family Office'
        elif 'fund' in lp_text or 'institutional' in lp_text:
            return 'Fund Investor'
        elif 'individual' in lp_text or 'angel' in lp_text or 'hnw' in lp_text:
            return 'HNW Individual'
        else:
            return 'GP Investor'
    
    def _calculate_confidence_score(self, lp: Dict) -> int:
        """Calculate confidence score (0-100) based on data completeness"""
        score = 0
        
        # Name present (required)
        if lp.get('name'):
            score += 30
        
        # Contact info present
        if lp.get('Email or website') or lp.get('Contact information') or lp.get('email'):
            score += 25
        
        # Investment focus described
        if lp.get('Investment focus/industries') or lp.get('Investment interests'):
            score += 20
        
        # Deal history present
        if lp.get('Notable deals or portfolio companies') or lp.get('Notable investments'):
            score += 15
        
        # Additional details
        if lp.get('Investment size preference') or lp.get('Preferences'):
            score += 10
        
        return min(score, 100)
    
    def _deduplicate_lps(self, lps: List[Dict]) -> List[Dict]:
        """Remove duplicate LPs based on firm name similarity"""
        unique_lps = []
        seen_names = set()
        
        for lp in lps:
            name_key = lp.get('Firm', lp.get('LP_Name', '')).lower().strip()
            
            if name_key and name_key not in seen_names:
                seen_names.add(name_key)
                unique_lps.append(lp)
        
        return unique_lps
