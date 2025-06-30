import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from urllib.parse import urlparse
from xlsxwriter import Workbook
import io
import json

# Configuration
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# Custom CSS to match your theme
def inject_css():
    css = """
    <style>
    :root {
        --primary-color: #000000;
        --secondary-color: #FD653D;
        --background: #f5f5f5;
        --background-color-light: #e7e7ff5e;
        --white-color: white;
        --border-color: #E6EDFF;
        --indigo-color: #FD653D;
        --red-color: #FF3B30;
        --green-color: #146356;
        --orange-color: #FF9500;
        --grey-color: #7C8DB5;
        --black: #09112c;
    }
    
    .dark-mode {
        --primary-color: white;
        --white-color: black;
        --black: white;
        --background: #050505;
        --background-color-light: #2b2b2b5e;
    }
    
    html, body, #root, .stApp {
        font-family: 'Poppins', sans-serif !important;
        background: var(--background) !important;
        color: var(--primary-color) !important;
    }
    
    /* Main container */
    .main .block-container {
        max-width: 1200px;
        padding: 2rem 1rem;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--primary-color) !important;
        font-weight: 700 !important;
        font-family: 'Poppins', sans-serif !important;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: var(--indigo-color) !important;
        color: white !important;
        border-radius: 5px !important;
        border: none !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        margin: 0 !important;
    }
    
    .stButton>button:hover {
        opacity: 0.9 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
    }
    
    /* Button container */
    .stButton {
        display: flex !important;
        flex-direction: column !important;
        gap: 5px !important;
        width: 100% !important;
    }
    
    /* File uploader */
    .stFileUploader>div>div {
        border: 2px dashed var(--grey-color) !important;
        border-radius: 10px !important;
        background: var(--background-color-light) !important;
    }
    
    /* Beautiful table styling */
    .stDataFrame {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }
    
    .stDataFrame table {
        width: 100% !important;
        border-collapse: collapse !important;
        box-sizing: border-box !important;
    }
    
    .stDataFrame th {
        background: var(--indigo-color) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 12px 15px !important;
        text-align: left !important;
    }
    
    .stDataFrame td {
        padding: 10px 15px !important;
        border-bottom: 1px solid var(--border-color) !important;
        vertical-align: middle !important;
    }
    
    .stDataFrame tr:hover td {
        background: var(--background-color-light) !important;
    }
    
    .stDataFrame tr:last-child td {
        border-bottom: none !important;
    }
    
    /* Status indicators */
    .status-live {
        color: var(--green-color) !important;
        font-weight: bold !important;
    }
    
    .status-down {
        color: var(--red-color) !important;
        font-weight: bold !important;
    }
    
    .status-error {
        color: var(--orange-color) !important;
        font-weight: bold !important;
    }
    
    .status-likely {
        color: var(--indigo-color) !important;
        font-weight: bold !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background-color: var(--indigo-color) !important;
    }
    
    /* Metrics */
    .stMetric {
        background: var(--background-color-light) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
        border: 1px solid var(--border-color) !important;
    }
    
    .stMetric label {
        color: var(--grey-color) !important;
        font-weight: 500 !important;
    }
    
    .stMetric div {
        color: var(--primary-color) !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }
    
    /* Expander */
    .stExpander {
        background: var(--background-color-light) !important;
        border-radius: 10px !important;
        border: 1px solid var(--border-color) !important;
    }
    
    .stExpander label {
        color: var(--primary-color) !important;
        font-weight: 600 !important;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--background-color-light);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--grey-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--indigo-color);
    }
    
    /* Custom classes for your specific elements */
    .logo-text {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700 !important;
        color: var(--indigo-color) !important;
    }
    
    .logo-text span {
        color: var(--black) !important;
    }
    
    /* Download buttons container */
    .download-buttons {
        display: flex;
        flex-direction: column;
        gap: 5px;
        width: 100%;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    
    <link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet" />
    """
    st.markdown(css, unsafe_allow_html=True)

# Normalize URL
def validate_url(url):
    parsed = urlparse(url)
    if not parsed.scheme:
        return 'http://' + url
    return url

# Check websites using GET (reliable)
def check_websites(df, url_column):
    results = []
    progress_bar = st.progress(0)
    total_urls = len(df)
    
    for index, row in df.iterrows():
        try:
            url = row[url_column]
            validated_url = validate_url(url)
            start_time = time.time()
            response = requests.get(
                validated_url,
                headers=HEADERS,
                allow_redirects=True,
                timeout=10,
                stream=True
            )
            latency = round((time.time() - start_time) * 1000, 2)
            code = response.status_code

            if code < 400:
                status = "Live"
            elif code in [403, 429]:
                status = "Likely Live"
            else:
                status = "Down"

            # Create a new row with all original data plus status info
            result_row = row.to_dict()
            result_row.update({
                'status_code': code,
                'status': status,
                'latency_ms': latency,
                'checked_url': validated_url
            })
            results.append(result_row)

        except Exception as e:
            # Create a new row with all original data plus error info
            result_row = row.to_dict()
            result_row.update({
                'status_code': None,
                'status': 'Error',
                'latency_ms': None,
                'checked_url': url
            })
            results.append(result_row)
        
        # Update progress
        progress = (index + 1) / total_urls
        progress_bar.progress(progress)
    
    progress_bar.empty()
    return pd.DataFrame(results)

# Detect URL column automatically
def detect_url_column(df):
    url_columns = []
    for col in df.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in ['url', 'website', 'domain', 'link', 'site']):
            url_columns.append(col)
    
    if url_columns:
        return url_columns[0]  # Return the first matching column
    return df.columns[0]  # Fallback to first column if no URL column found

def create_download_buttons(df):
    """Create download buttons with custom styling"""
    st.markdown("""
    <style>
    .download-btn {
        background: var(--indigo-color) !important;
        color: white !important;
        border-radius: 5px !important;
        padding: 0.5rem 1rem !important;
        border: none !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        text-align: center !important;
    }
    .download-btn:hover {
        opacity: 0.9 !important;
        transform: translateY(-2px) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("### Export Results")
    
    # Create a single column layout for buttons
    with st.container():
        # Excel download
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button(
            label="📊 Download Excel",
            data=excel_buffer.getvalue(),
            file_name="website_status_results.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            key="excel_download"
        )
        
        # CSV download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📝 Download CSV",
            data=csv,
            file_name="website_status_results.csv",
            mime='text/csv',
            key="csv_download"
        )
        
        # JSON download
        json_data = df.to_json(orient='records', indent=2)
        st.download_button(
            label="📄 Download JSON",
            data=json_data,
            file_name="website_status_results.json",
            mime='application/json',
            key="json_download"
        )

# Main app function
def main():
    st.set_page_config(
        page_title="Website Status Checker Pro",
        layout="centered",
        page_icon="🌐"
    )
    inject_css()
    st.markdown("Upload a CSV or Excel file containing website URLs to check their status while preserving all original data.")

    if 'results' not in st.session_state:
        st.session_state.results = pd.DataFrame()
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'original_df' not in st.session_state:
        st.session_state.original_df = None

    with st.expander("📁 Upload CSV/Excel File", expanded=True):
        uploaded_file = st.file_uploader(
            "Choose a file with URLs (CSV or Excel)", 
            type=['csv', 'xlsx', 'xls'],
            help="File should contain at least one column with website URLs"
        )

        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:  # Excel files
                    df = pd.read_excel(uploaded_file)
                
                if df.empty:
                    st.error("The uploaded file is empty")
                    return
                
                # Detect URL column automatically
                url_column = detect_url_column(df)
                st.session_state.url_column = url_column
                st.session_state.original_df = df
                
                st.success(f"Found {len(df)} records. URL column detected: '{url_column}'")
                st.write("Preview of your data:")
                st.dataframe(df.head(3))

            except Exception as e:
                st.error(f"Error reading file: {str(e)}")

    # Action buttons in a single column with gap
    with st.container():
        if st.button(
            "🚀 Start Checking", 
            disabled='original_df' not in st.session_state or st.session_state.processing,
            help="Check status of all websites in the file"
        ):
            st.session_state.processing = True
            with st.spinner("Checking websites..."):
                st.session_state.results = check_websites(
                    st.session_state.original_df, 
                    st.session_state.url_column
                )
                st.session_state.processing = False
                st.success("Website checking complete!")
        
        if st.button(
            "🔄 Clear Results", 
            disabled=st.session_state.results.empty,
            help="Clear all results and start over"
        ):
            st.session_state.results = pd.DataFrame()
            st.session_state.original_df = None
            st.experimental_rerun()

    if not st.session_state.results.empty:
        # Download options
        st.markdown("___")
        create_download_buttons(st.session_state.results)
        
        # Status summary stats
        st.markdown('<h2 style="color: var(--primary-color);">Results</h2>', unsafe_allow_html=True)
        status_counts = st.session_state.results['status'].value_counts()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("✅ Live", status_counts.get('Live', 0))
        col2.metric("⚠️ Likely Live", status_counts.get('Likely Live', 0))
        col3.metric("❌ Down", status_counts.get('Down', 0))
        col4.metric("🚨 Errors", status_counts.get('Error', 0))

        def status_icon(status):
            return {
                'Live': "🟢",
                'Down': "🔴",
                'Likely Live': "🔵",
                'Error': "🟡"
            }.get(status, "❓")

        # Prepare display dataframe
        display_df = st.session_state.results.copy()
        display_df['Status'] = display_df['status'].apply(
            lambda x: f"<span class='status-{x.lower().replace(' ', '-')}'>{status_icon(x)} {x}</span>"
        )
        
        # Reorder columns to show status info first
        cols_to_show = ['Status', 'status_code', 'latency_ms', 'checked_url'] + [
            col for col in display_df.columns 
            if col not in ['Status', 'status_code', 'latency_ms', 'checked_url', 'status']
        ]
        
        # Display the beautiful table
        st.dataframe(
            display_df[cols_to_show],
            use_container_width=True,
            hide_index=True
        )

if __name__ == '__main__':
    main()
