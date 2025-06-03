import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import base64

# Configuration
FLASK_ENDPOINT = "http://localhost:5000/check"
CSS_FILE = "http://localhost:5000/static/styles.css"

# Custom CSS injection function
def inject_css(css_file):
    try:
        # Try fetching from Flask static files
        css = requests.get(css_file).text
    except:
        # Fallback to default CSS
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

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = pd.DataFrame()
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Main app function
def main():
    # Inject custom CSS
    inject_css(CSS_FILE)
    # File upload section\
    with st.expander("📁 Upload CSV File", expanded=True):
        uploaded_file = st.file_uploader(
            "Choose a CSV file with URLs",
            type=['csv'],
            help="File should contain one URL per line or a column named 'URL'"
        )
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                if 'URL' in df.columns:
                    urls = df['URL'].tolist()
                else:
                    urls = df.iloc[:, 0].tolist()
                
                st.success(f"Found {len(urls)} URLs in the file")
                st.session_state.urls = urls
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    # Control buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Start Checking", disabled=not hasattr(st.session_state, 'urls') or st.session_state.processing):
            st.session_state.processing = True
            with st.spinner("Checking websites..."):
                try:
                    response = requests.post(
                        FLASK_ENDPOINT,
                        json={'urls': st.session_state.urls}
                    )
                    if response.status_code == 200:
                        results = response.json()
                        st.session_state.results = pd.DataFrame(results)
                        st.session_state.last_updated = datetime.now()
                        st.success("Completed website checks!")
                    else:
                        st.error(f"API Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
                finally:
                    st.session_state.processing = False
    
    with col2:
        if st.button("🔄 Clear Results", disabled=st.session_state.results.empty):
            st.session_state.results = pd.DataFrame()
    
    # Results display
    if not st.session_state.results.empty:
        st.markdown("### Results")
        
        # Add status icons
        def status_icon(status):
            if status == 'Live': return "🟢"
            elif status == 'Down': return "🔴"
            else: return "🟡"
        
        display_df = st.session_state.results.copy()
        display_df['Status'] = display_df['status'].apply(
            lambda x: f"<span class='status-{x.lower()}'>{status_icon(x)} {x}</span>",
        )
        
        # Convert to HTML and display
        st.write(
            display_df[['original_url', 'Status', 'status_code', 'latency_ms']].to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
        
        # Download button
        csv = st.session_state.results.to_csv(index=False)
        st.download_button(
            label="💾 Download Results",
            data=csv,
            file_name=f"website_status_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv'
        )

if __name__ == '__main__':
    main()