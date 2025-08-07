import streamlit as st
import pandas as pd
import requests
import time
import streamlit.components.v1 as components
from datetime import datetime
from urllib.parse import urlparse
from xlsxwriter import Workbook
import io
import json

# Configuration
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}
st.set_page_config(layout="centered")
def validate_url(url):
    parsed = urlparse(url)
    if not parsed.scheme:
        return "http://" + url
    return url

# Main checking function
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
                stream=True,
            )
            latency = round((time.time() - start_time) * 1000, 2)
            code = response.status_code

            if code < 400:
                status = "Live"
            elif code in [403, 429]:
                status = "Likely Live"
            else:
                status = "Down"

            result_row = row.to_dict()
            result_row.update({
                "status_code": code,
                "status": status,
                "latency_ms": latency,
                "checked_url": validated_url,
            })
            results.append(result_row)

        except Exception:
            result_row = row.to_dict()
            result_row.update({
                "status_code": None,
                "status": "Error",
                "latency_ms": None,
                "checked_url": row[url_column],
            })
            results.append(result_row)

        progress_bar.progress((index + 1) / total_urls)

    progress_bar.empty()
    return pd.DataFrame(results)

def detect_url_column(df):
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ["url", "website", "domain", "link", "site"]):
            return col
    return df.columns[0]

    if url_columns:
        return url_columns[0]
    return df.columns[0]

def create_download_buttons(df):
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    st.download_button(
        label="Download Excel",
        data=excel_buffer.getvalue(),
        file_name="website_status_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="excel_download",
        use_container_width=True
    )

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="website_status_results.csv",
        mime="text/csv",
        key="csv_download",
        use_container_width=True
    )

    json_data = df.to_json(orient="records", indent=2)
    st.download_button(
        label="Download JSON",
        data=json_data,
        file_name="website_status_results.json",
        mime="application/json",
        key="json_download",
        use_container_width=True
    )

def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass  # Ignore if style file is missing

def main():
    local_css("style.css")

    if "results" not in st.session_state:
        st.session_state.results = pd.DataFrame()
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "original_df" not in st.session_state:
        st.session_state.original_df = None
    if "url_column" not in st.session_state:
        st.session_state.url_column = None

    uploaded_file = st.file_uploader(
        "Upload a file and check the live status of websites in bulk.",
        type=["csv", "xlsx", "xls"],
        help="Ensure the file contains a column with website URLs.",
    )

    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            if df.empty:
                st.error("The uploaded file is empty.")
                return

            # Detect suggestion column
            suggested_column = detect_url_column(df)

            # Let user select the actual column
            st.session_state.url_column = st.selectbox(
                "Select the column that contains the website URLs:",
                options=df.columns.tolist(),
                index=df.columns.tolist().index(suggested_column),
            )

            st.session_state.original_df = df
            st.success(f"File loaded with {len(df)} records.")
            st.write("Data preview:")
            st.dataframe(df.head(5), use_container_width=True)

        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

    # Buttons in one row
    with st.container():
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(
                "Start Checking",
                use_container_width=True,
                help="Start checking the status of all websites.",
            ):
                st.session_state.processing = True
                with st.spinner("Checking websites..."):
                    st.session_state.results = check_websites(
                        st.session_state.original_df,
                        st.session_state.url_column,
                    )
                    st.session_state.processing = False
                    st.success("Website status checking complete!")

        with col2:
            if st.button(
                "Clear Results",
                use_container_width=True,
                disabled=st.session_state.results.empty,
                help="Reset and upload a new file.",
            ):
                st.session_state.results = pd.DataFrame()
                st.session_state.original_df = None
                st.session_state.url_column = None
                st.rerun()

    if not st.session_state.results.empty:
        st.markdown("___")
        create_download_buttons(st.session_state.results)

        st.markdown('<hr>', unsafe_allow_html=True)
        st.markdown('<p style="color: var(--primary-color);">Results Summary</p>', unsafe_allow_html=True)
        
        status_counts = st.session_state.results["status"].value_counts()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Live", status_counts.get("Live", 0))
        col2.metric("Likely Live", status_counts.get("Likely Live", 0))
        col3.metric("Down", status_counts.get("Down", 0))
        col4.metric("Errors", status_counts.get("Error", 0))

        def status_icon(status):
            return {"Live": "🟢", "Down": "🔴", "Likely Live": "🔵", "Error": "🟡"}.get(status, "?")

        display_df = st.session_state.results.copy()
        display_df["Status"] = display_df["status"].apply(lambda x: f"{status_icon(x)} {x}")

        cols_to_show = ["Status", "status_code", "latency_ms", "checked_url"] + [
            col for col in display_df.columns if col not in ["Status", "status_code", "latency_ms", "checked_url", "status"]
        ]

        st.dataframe(display_df[cols_to_show], use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
