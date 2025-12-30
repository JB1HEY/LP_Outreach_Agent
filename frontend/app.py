import streamlit as st
import pandas as pd
import os
import sys

# Add parent directory to path to allow importing from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import InvestmentCriteria, SearchConfig, load_config
from src.discovery import LPDiscoveryEngine
from src.agent import LPOutreachAgent
from src.targets import DailyTargetGenerator

# Set page config to use default light theme (White background, Black text)
st.set_page_config(
    page_title="LP Discovery Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to ensure high contrast black/white
st.markdown("""
<style>
    .reportview-container {
        background: #ffffff;
        color: #000000;
    }
    .sidebar .sidebar-content {
        background: #f0f2f6;
    }
    h1, h2, h3 {
        color: #000000;
    }
    .stButton>button {
        color: #ffffff;
        background-color: #000000;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🔍 LP Discovery Agent")
    st.markdown("Automated Investor Discovery System")
    
    # helper to load config
    _, default_criteria = load_config()
    
    # --- Sidebar: Configuration ---
    st.sidebar.header("Configuration")
    
    # API Key Handling
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
        if not api_key:
            st.warning("Please provide an API Key in .env or sidebar to proceed.")
            st.stop()
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Search Settings")
    depth = st.sidebar.select_slider("Search Depth", options=["quick", "comprehensive"], value="quick")
    max_results = st.sidebar.slider("Max Results per Category", 5, 50, 10)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Target Categories")
    cat_gp = st.sidebar.checkbox("GP Investors", value=True)
    cat_fund = st.sidebar.checkbox("Fund Investors", value=True)
    cat_hnw = st.sidebar.checkbox("HNW Individuals", value=True)
    cat_family = st.sidebar.checkbox("Family Offices", value=True)
    
    selected_categories = []
    if cat_gp: selected_categories.append("GP Investor")
    if cat_fund: selected_categories.append("Fund Investor")
    if cat_hnw: selected_categories.append("HNW Individual")
    if cat_family: selected_categories.append("Family Office")
    
    # --- Main Content: Investment Criteria ---
    st.subheader("Investment Criteria")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Financials")
        
        # EBITDA
        use_ebitda = st.checkbox("Filter by EBITDA Range", value=True)
        ebitda_default = (float(default_criteria.ebitda_range[0]), float(default_criteria.ebitda_range[1]))
        ebitda_min, ebitda_max = st.slider(
            "EBITDA ($M)", 
            min_value=0.0, 
            max_value=50.0, 
            value=ebitda_default, 
            step=0.5,
            disabled=not use_ebitda
        )
        
        # Revenue
        use_revenue = st.checkbox("Filter by Revenue Range", value=True)
        rev_default = (float(default_criteria.revenue_range[0]), float(default_criteria.revenue_range[1]))
        rev_min, rev_max = st.slider(
            "Revenue ($M)", 
            min_value=0.0, 
            max_value=500.0, 
            value=rev_default, 
            step=1.0,
            disabled=not use_revenue
        )

    with col2:
        st.markdown("### Focus Area")
        
        # Industries
        use_industries = st.checkbox("Filter by Specific Industries", value=True)
        default_industries = default_criteria.industries if default_criteria.industries else ["SaaS", "Fintech", "Healthcare IT"]
        industries_input = st.text_area(
            "Target Industries (comma separated)", 
            ", ".join(default_industries),
            disabled=not use_industries,
            help="Enter industries like: SaaS, AI, Manufacturing"
        )
        
        # Preferences
        use_preferences = st.checkbox("Include Investment Preferences", value=True)
        default_prefs = default_criteria.preferences if default_criteria.preferences else ["emerging_managers", "special_situations"]
        preferences_input = st.text_input(
            "Preferences (comma separated)",
            ", ".join(default_prefs),
            disabled=not use_preferences
        )

    # --- Action Area ---
    st.markdown("---")
    
    if st.button("🚀 Start Discovery", type="primary", use_container_width=True):
        if not selected_categories:
            st.error("Please select at least one target category in the sidebar.")
            st.stop()
            
        # Build Criteria Object
        criteria = InvestmentCriteria(
            use_ebitda=use_ebitda,
            use_revenue=use_revenue,
            use_industries=use_industries,
            use_preferences=use_preferences,
            ebitda_range=(ebitda_min, ebitda_max),
            revenue_range=(rev_min, rev_max),
            industries=[i.strip() for i in industries_input.split(",") if i.strip()],
            preferences=[p.strip() for p in preferences_input.split(",") if p.strip()]
        )
        
        # Build Search Config
        config = SearchConfig(
            gemini_api_key=api_key,
            max_results_per_search=max_results,
            search_depth=depth,
            categories=selected_categories
        )
        
        # Run Discovery
        with st.status("Running Discovery Process...", expanded=True) as status:
            try:
                st.write("Initializing Gemini Engine...")
                engine = LPDiscoveryEngine(api_key)
                
                st.write(f"Searching for LPs across {len(selected_categories)} categories...")
                results = engine.search_lps(criteria, config)
                
                if not results:
                    status.update(label="Discovery Complete - No Results Found", state="error")
                    st.warning("No LPs found matching your criteria. Try broadening your search.")
                else:
                    status.update(label="Discovery Complete!", state="complete")
                    st.success(f"Found {len(results)} potential investors!")
                    
                    # Store results in session state to persist
                    st.session_state['results'] = results
                    
            except Exception as e:
                status.update(label="Error Occurred", state="error")
                st.error(f"An error occurred: {str(e)}")
                if "429" in str(e):
                    st.error("Quota Exceeded. Please check your API plan or wait a few minutes.")

    # --- Results Display ---
    if 'results' in st.session_state:
        results = st.session_state['results']
        
        st.subheader("Discovered LPs")
        
        # Convert to DataFrame for display
        df = pd.DataFrame(results)
        
        # Show interactive table
        st.dataframe(
            df[['LP_Name', 'Firm', 'LP_Category', 'Confidence_Score', 'Email', 'Interests']],
            use_container_width=True,
            hide_index=True
        )
        
        # Import Action
        col_import, col_dl = st.columns(2)
        with col_import:
            if st.button("💾 Save to Database"):
                agent = LPOutreachAgent()
                count = agent.import_discovered_lps(results)
                st.success(f"Successfully saved {count} new LPs to lp_database.csv")
                
        with col_dl:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download raw CSV",
                csv,
                "discovered_lps.csv",
                "text/csv",
                key='download-csv'
            )
        
        # --- Recommended Email Template ---
        st.markdown("---")
        st.subheader("📧 Recommended Introduction Email Template")
        st.markdown("Use this template as a starting point for your LP outreach:")
        
        email_template = """Subject: Introduction - [Your Fund Name] - [Brief Value Proposition]

Dear [LP Name],

I hope this message finds you well. I'm reaching out because [Your Fund Name] aligns with [Firm Name]'s investment focus in [relevant industry/focus area].

**About [Your Fund Name]:**
[Brief 2-3 sentence description of your fund, strategy, and key differentiators]

**Why This May Be of Interest:**
- [Specific reason 1 related to their investment criteria/interests]
- [Specific reason 2 related to their portfolio or focus areas]
- [Specific reason 3 - track record, unique opportunity, etc.]

I would welcome the opportunity to discuss how [Your Fund Name] might fit within [Firm Name]'s portfolio. Would you be available for a brief call in the coming weeks?

Thank you for your consideration, and I look forward to the possibility of connecting.

Best regards,
[Your Name]
[Your Title]
[Your Fund Name]
[Your Contact Information]"""
        
        st.text_area(
            "Email Template",
            email_template,
            height=400,
            help="Copy and customize this template for your outreach. Remember to personalize each email based on the specific LP's interests and background."
        )
        
        # Copy button functionality
        if st.button("📋 Copy Email Template"):
            st.code(email_template, language=None)
            st.success("Template displayed above. Select and copy the text to use it.")

if __name__ == "__main__":
    main()
