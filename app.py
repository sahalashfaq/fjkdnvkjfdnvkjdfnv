import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from urllib.parse import urlparse

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
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Normalize URL
def validate_url(url):
    parsed = urlparse(url)
    if not parsed.scheme:
        return 'http://' + url
    return url

# Check websites using GET (reliable)
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
            code = response.status_code

            if code < 400:
                status = "Live"
            elif code in [403, 429]:
                status = "Likely Live"
            else:
                status = "Down"

            results.append({
                'original_url': url,
                'status_code': code,
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

# Main app function
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
                st.success("Website checking complete.")
        if st.button("🔄 Clear Results", disabled=st.session_state.results.empty):
            st.session_state.results = pd.DataFrame()

    if not st.session_state.results.empty:
        st.markdown("Results")

        def status_icon(status):
            return {
                'Live': "🟢",
                'Down': "🔴",
                'Likely Live': "🔵",
                'Error': "🟡"
            }.get(status, "❓")

        display_df = st.session_state.results.copy()
        display_df['Status'] = display_df['status'].apply(
            lambda x: f"<span class='status-{x.lower().replace(' ', '-')}'>{status_icon(x)} {x}</span>"
        )

        st.write(
            display_df[['original_url', 'Status', 'status_code', 'latency_ms']].to_html(escape=False, index=False),
            unsafe_allow_html=True
        )

        csv = st.session_state.results.to_csv(index=False)
        file_name=f"website_status.csv"
        st.download_button(
            label="💾 Download Results",
            data=csv,
            file_name=file_name,
            mime='text/csv'
        )

if __name__ == '__main__':
    main()
