# LP Outreach Agent

An intelligent Python tool for discovering and managing outreach to Limited Partners (LPs) in venture capital contexts. **Now with automated LP discovery using Gemini AI!**

## Features

- **🤖 Automated LP Discovery**: Use Gemini API to automatically find and categorize LPs based on your investment criteria
- **📊 LP Database Management**: Store and track LP details with comprehensive fields
- **🎯 Daily Target Lists**: Generate prioritized outreach lists with intelligent scoring
- **📧 Personalized Outreach**: Create customized email templates based on LP profiles
- **📈 Interaction Tracking**: Log all communications and automatically update LP status
- **🏷️ Smart Categorization**: Automatically group LPs into GP investors, Fund investors, HNW individuals, and Family offices
- **💾 Data Persistence**: All data saved to CSV for easy editing and backup

## Installation

Requires Python 3.7+ and dependencies:

```bash
pip install -r requirements.txt
```

Dependencies:
- pandas>=1.3.0
- google-generativeai>=0.3.0
- python-dotenv>=0.19.0

## Quick Start - Automated Discovery

### 1. Configure Your Search Criteria

Run the interactive setup:

```bash
python run_discovery.py --customize
```

Or manually edit `lp_config.json`:

```json
{
  "search_config": {
    "gemini_api_key": "YOUR_API_KEY",
    "max_results_per_search": 20,
    "search_depth": "comprehensive"
  },
  "investment_criteria": {
    "ebitda_range": [1, 5],
    "revenue_range": [20, 150],
    "industries": ["SaaS", "Fintech", "Healthcare IT"],
    "company_targets": ["B2B Software", "Enterprise Solutions"],
    "preferences": ["emerging_managers", "special_situations"]
  }
}
```

### 2. Run Automated Discovery

```bash
python run_discovery.py
```

This will:
1. Search for LPs matching your criteria using Gemini AI
2. Categorize them into 4 groups (GP, Fund, HNW, Family Office)
3. Import to your database
4. Generate a daily target list
5. Export results to CSV and markdown report

### 3. Review Your Daily Targets

Check the generated files:
- `daily_targets_YYYY-MM-DD.csv` - Spreadsheet of prioritized LPs
- `daily_targets_report_YYYY-MM-DD.md` - Detailed report with talking points

## Manual Usage

You can also use the agent programmatically:

```python
from agent import LPOutreachAgent
from daily_targets import DailyTargetGenerator

# Initialize agent
agent = LPOutreachAgent()

# Manually add an LP
agent.add_lp(
    name="John Doe",
    firm="Family Office Inc.",
    email="john@example.com",
    interests="AI, Climate Tech",
    lp_category="Family Office",
    ebitda_range="$1M-$5M",
    revenue_range="$20M-$150M",
    investment_preferences="emerging_managers, special_situations"
)

# Generate daily targets
generator = DailyTargetGenerator(agent)
targets = generator.generate_targets(
    target_count=10,
    min_confidence=50,
    prioritize_category="Family Office"
)

# Export to CSV
generator.export_to_csv(targets)

# Create report
report = generator.create_summary_report(targets)
print(report)
```

## LP Categories

The system automatically categorizes LPs into:

1. **GP Investor**: General Partners and VC firms that invest in companies
2. **Fund Investor**: Institutional LPs that invest in VC/PE funds
3. **HNW Individual**: High Net Worth individuals and angel investors
4. **Family Office**: Family offices investing in companies or funds

## Investment Criteria

Configure your search with:

- **EBITDA Range**: Target company EBITDA (default: $1M-$5M)
- **Revenue Range**: Target company revenue (default: $20M-$150M)
- **Industries**: Specific sectors (e.g., SaaS, Fintech, Healthcare IT)
- **Company Targets**: Company types (e.g., B2B Software, Enterprise Solutions)
- **Preferences**: 
  - `emerging_managers` - Willing to invest in first-time fund managers
  - `special_situations` - Interested in distressed assets, turnarounds, etc.

## Daily Target List

The target generator uses intelligent priority scoring based on:

- **Confidence Score** (0-100%): Data quality and completeness
- **Status**: Prospects prioritized over already-contacted LPs
- **Category Balance**: Ensures diversity across LP types
- **Recency**: Recently discovered LPs get a boost
- **Deal History**: LPs with notable deals score higher

## LP Status Workflow

The agent automatically tracks LP progression:

1. **Prospect** → Initial Outreach needed
2. **Contacted** → Follow-up in 1 week
3. **Engaged** → Schedule Meeting
4. **In Discussion** → Send Deck

## Data Storage

All LP data is stored in `lp_database.csv` with fields:

**Core Fields:**
- LP_Name, Firm, Email, Interests
- Status, Last_Contact, Next_Action, Notes

**Discovery Fields:**
- LP_Category, EBITDA_Range, Revenue_Range
- Investment_Preferences, Industries, Deal_History
- Discovery_Date, Confidence_Score

## Advanced Features

### Filter LPs by Criteria

```python
# Get all Family Offices with high confidence
family_offices = agent.filter_by_criteria(
    category="Family Office",
    min_confidence=70,
    industries=["SaaS", "Fintech"],
    status="Prospect"
)
```

### Get LPs by Category

```python
categories = agent.get_lps_by_category()
for category, lps in categories.items():
    print(f"{category}: {len(lps)} LPs")
```

### Track Interactions

```python
agent.log_interaction(
    "John Doe",
    "Initial Outreach",
    "Sent intro email via warm introduction from Sarah"
)
```

## Best Practices

- **Verify Discovered Data**: AI-generated results should be manually verified before outreach
- **Refine Search Criteria**: Adjust industries and preferences based on initial results
- **Track Response Rates**: Monitor which LP categories respond best
- **Personalize Outreach**: Use deal history and preferences in your messaging
- **Respect Privacy**: Ensure compliance with data protection regulations (GDPR, CCPA)
- **Manage API Costs**: Use "quick" search depth for exploratory searches

## API Key Security

**Important**: Never commit your API key to version control!

Options for secure key storage:
1. Use `lp_config.json` (add to `.gitignore`)
2. Set environment variable: `export GEMINI_API_KEY="your_key"`
3. Use a secrets management system for production

## Troubleshooting

**No LPs discovered?**
- Check your API key is valid
- Try broader search criteria (fewer industries, wider ranges)
- Use "comprehensive" search depth

**Low confidence scores?**
- Normal for automated discovery
- Set `min_confidence=40` for more results
- Manually verify and enrich data

**Duplicate LPs?**
- System deduplicates by firm name
- Check `lp_database.csv` and remove manually if needed

## Extending the Tool

Consider adding:
- Email sending via SMTP or SendGrid API
- Calendar integration for scheduling meetings
- CRM integration (Affinity, 4Degrees)
- Webhook notifications for new discoveries
- Machine learning for response prediction

## License

Open source - use and modify as needed for your fund operations.