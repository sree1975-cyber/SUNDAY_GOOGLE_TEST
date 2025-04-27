import streamlit as st
from streamlit_option_menu import option_menu
from utils.data_manager import init_data, save_data
from utils.ui_components import display_header, login_form, add_link_section, browse_section, download_section
from utils.link_operations import save_link, delete_selected_links, fetch_metadata
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Verify Streamlit version
if st.__version__ != "1.31.0":
    st.error(f"Streamlit version {st.__version__} detected. This app requires 1.31.0. Check Cloud logs or contact support.")

# Set page configuration
st.set_page_config(
    page_title="Web Content Manager",
    page_icon="🔖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .header {
        background: linear-gradient(135deg, #6e8efb, #a777e3);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .dataframe {
        width: 100%;
    }
    .tag {
        display: inline-block;
        background: #e0e7ff;
        color: #4f46e5;
        padding: 0.2rem 0.5rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        margin-right: 0.5rem;
        margin-bottom: 0.3rem;
    }
    .delete-btn {
        background-color: #ff4b4b !important;
        color: white !important;
        margin-top: 0.5rem;
    }
    .mode-indicator {
        background: #e0e7ff;
        color: #4f46e5;
        padding: 0.5rem;
        border-radius: 5px;
        margin-bottom: 1rem;
        font-weight: bold;
        text-align: center;
    }
    .exit-btn {
        background-color: #ff4b4b !important;
        color: white !important;
        width: 100%;
        margin-top: 1rem;
    }
    .login-btn {
        background-color: #6e8efb !important;
        color: white !important;
        width: 100%;
        margin-top: 1rem;
    }
    .login-container {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        max-width: 500px;
        margin: 2rem auto;
    }
    .login-title {
        text-align: center;
        color: #4f46e5;
        margin-bottom: 1rem;
    }
    .login-info {
        text-align: center;
        color: #666;
        margin-bottom: 1.5rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
    }
    .login-btn:hover {
        background-color: #5a7de3 !important;
    }
    .public-btn {
        background-color: #10b981 !important;
        color: white !important;
    }
    .public-btn:hover {
        background-color: #0e9f6e !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main function to run the Web Content Manager app"""
    # Check if logged in
    if 'mode' not in st.session_state:
        login_form()
        return
    
    mode = st.session_state['mode']
    username = st.session_state.get('username')
    
    # Sidebar with Exit button and navigation
    with st.sidebar:
        st.markdown(f"""
        <p style='color: {"green" if mode == "owner" else "blue" if mode == "guest" else "gray"}; font-weight: bold;'>
            {mode.capitalize()} Mode{f" ({username})" if username else ""}
        </p>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Exit and Clear Cache", key="exit_button", help="Clear all session data and reset the app"):
            logging.debug(f"Exit button clicked. Session state before clear: {st.session_state}")
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state['password_input_counter'] = 0
            st.session_state['username_input_counter'] = 0
            st.success("✅ Session cleared! App will reset.")
            st.balloons()
            st.rerun()
        
        st.markdown("""
        <div style="padding: 1rem;">
            <h2 style="margin-bottom: 1.5rem;">Navigation</h2>
        </div>
        """, unsafe_allow_html=True)
        
        selected = option_menu(
            menu_title=None,
            options=["Add Link", "Browse Links", "Export Data"],
            icons=['plus-circle', 'book', 'download'],
            default_index=0,
            styles={
                "container": {"padding": "0!important"},
                "icon": {"color": "#6e8efb", "font-size": "1rem"}, 
                "nav-link": {"font-size": "1rem", "text-align": "left", "margin": "0.5rem 0", "padding": "0.5rem 1rem"},
                "nav-link-selected": {"background-color": "#6e8efb", "font-weight": "normal"},
            }
        )
    
    # Initialize data based on mode
    if mode in ["owner", "guest"]:
        if 'df' not in st.session_state or st.session_state.get('username') != username:
            df, excel_file = init_data(mode, username)
            st.session_state['df'] = df
            st.session_state['excel_file'] = excel_file
            st.session_state['username'] = username
        else:
            df = st.session_state['df']
            excel_file = st.session_state['excel_file']
    else:
        df, excel_file = pd.DataFrame(), None
        if 'user_df' not in st.session_state:
            st.session_state['user_df'] = pd.DataFrame(columns=[
                'id', 'url', 'title', 'description', 'tags', 
                'created_at', 'updated_at'
            ])
    
    # Display header with mode indicator
    display_header(mode, username)
    
    # About section
    with st.expander("ℹ️ About Web Content Manager", expanded=False):
        st.markdown("""
        <div style="padding: 1rem;">
            <h3>Your Personal Web Library</h3>
            <p>Web Content Manager helps you save and organize web links with:</p>
            <ul>
                <li>📌 One-click saving of important web resources</li>
                <li>🏷️ <strong>Smart tagging</strong> - Automatically suggests tags</li>
                <li>🔍 <strong>Powerful search</strong> - Full-text search with tag filtering</li>
                <li>🗑️ <strong>Delete functionality</strong> - Remove unwanted links</li>
                <li>📊 <strong>Data Table View</strong> - View links in a table</li>
                <li>📥 <strong>Export capability</strong> - Download as Excel</li>
                <li>💾 <strong>Storage</strong> - Owner/guest data persists in Google Drive; public data is temporary</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Render selected section
    if selected == "Add Link":
        updated_df = add_link_section(df, excel_file, mode)
        if mode == "public":
            st.session_state['user_df'] = updated_df
        else:
            st.session_state['df'] = updated_df
    elif selected == "Browse Links":
        browse_section(df, excel_file, mode)
    elif selected == "Export Data":
        download_section(df, excel_file, mode)

if __name__ == "__main__":
    main()