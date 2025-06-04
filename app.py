import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from urllib.parse import urlparse
from xlsxwriter import Workbook
# Configuration
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# Inject custom CSS
def inject_css():
    css = """
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .status-live {
        color: #28a745;
        font-weight: bold;
    }
    .status-down {
        color: #dc3545;
        font-weight: bold;
    }
    .status-error {
        color: #ffc107;
        font-weight: bold;
    }
    .status-likely {
        color: #17a2b8;
        font-weight: bold;
    }
    .stProgress > div > div > div > div {
        background-color: #28a745;
    }
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

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

# Main app function
def main():
    st.set_page_config(page_title="Website Status Checker Pro", layout="centered")
    inject_css()
    st.markdown("Upload a CSV file containing website URLs to check their status while preserving all original data.")

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

    col1, col2 = st.columns(2)
    with col1:
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
        # Download options
        # st.markdown("### 💾 Download Results")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("___")
            # CSV download
            csv = st.session_state.results.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name="website_status_results.csv",
                mime='text/csv'
            )
            # Excel download
            excel_buffer = pd.ExcelWriter("website_status_results.xlsx", engine='xlsxwriter')
            st.session_state.results.to_excel(excel_buffer, index=False)
            excel_buffer.close()
            with open("website_status_results.xlsx", "rb") as f:
                st.download_button(
                    label="Download as Excel",
                    data=f,
                    file_name="website_status_results.xlsx",
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
    if not st.session_state.results.empty:
        st.markdown("___")
        st.markdown('<p style="font-size: 30px;font-weight:600;">Results</p>', unsafe_allow_html=True)
        # Status summary stats
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
        
        st.write(
            display_df[cols_to_show].to_html(escape=False, index=False),
            unsafe_allow_html=True
        )


if __name__ == '__main__':
    main()
