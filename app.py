import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from urllib.parse import urlparse

# Constants
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
HEADERS = {'User-Agent': USER_AGENT}

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
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Validate and normalize URL
def validate_url(url):
    parsed = urlparse(url)
    if not parsed.scheme:
        url = 'http://' + url
    return url

def check_websites(urls):
    results = []
    for url in urls:
        try:
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

            status_code = response.status_code
            if status_code < 400:
                status = "Live"
            elif status_code in [403, 429]:
                status = "Likely Live"  # Blocked by bot protection
            else:
                status = "Down"

            results.append({
                'original_url': url,
                'status_code': status_code,
                'status': status,
                'latency_ms': latency
            })

        except Exception as e:
            results.append({
                'original_url': url,
                'status_code': None,
                'status': 'Error',
                'latency_ms': None
            })
    return pd.DataFrame(results)

# Main app
def main():
    st.set_page_config(page_title="Website Status Checker", layout="centered")
    inject_css()

    if 'results' not in st.session_state:
        st.session_state.results = pd.DataFrame()
    if 'processing' not in st.session_state:
        st.session_state.processing = False

    with st.expander("📁 Upload CSV File", expanded=True):
        uploaded_file = st.file_uploader("Choose a CSV file with URLs", type=['csv'])

        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                urls = df['URL'].tolist() if 'URL' in df.columns else df.iloc[:, 0].tolist()
                st.success(f"Found {len(urls)} URLs")
                st.session_state.urls = urls
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Start Checking", disabled='urls' not in st.session_state or st.session_state.processing):
            st.session_state.processing = True
            with st.spinner("Checking websites..."):
                st.session_state.results = check_websites(st.session_state.urls)
                st.session_state.processing = False
                st.success("Check completed.")

    with col2:
        if st.button("🔄 Clear Results", disabled=st.session_state.results.empty):
            st.session_state.results = pd.DataFrame()

    if not st.session_state.results.empty:
        st.markdown("### Results")

        def status_icon(status):
            if status == 'Live': return "🟢"
            elif status == 'Down': return "🔴"
            else: return "🟡"

        display_df = st.session_state.results.copy()
        display_df['Status'] = display_df['status'].apply(
            lambda x: f"<span class='status-{x.lower()}'>{status_icon(x)} {x}</span>",
        )

        st.write(display_df[['original_url', 'Status', 'status_code', 'latency_ms']].to_html(escape=False, index=False), unsafe_allow_html=True)

        csv = st.session_state.results.to_csv(index=False)
    st.download_button(
    label="💾 Download Results",
    data=csv,
    file_name=f"website_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime='text/csv'
)


if __name__ == '__main__':
    main()
