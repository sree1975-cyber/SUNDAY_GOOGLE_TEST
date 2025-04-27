import streamlit as st
from utils.link_operations import fetch_metadata, save_link, delete_selected_links
import pandas as pd
import logging
import time
from io import BytesIO
from html import escape

def display_header(mode, username=None):
    """
    Display the app header with mode indicator.
    
    Args:
        mode (str): 'owner', 'guest', or 'public'
        username (str, optional): Username for guest mode
    """
    mode_text = "Public Mode"
    if mode == "owner":
        mode_text = "Logged in as Owner"
    elif mode == "guest":
        mode_text = f"Logged in as Guest: {username}"
    
    st.markdown(f"""
    <div class="mode-indicator">
        {mode_text}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="header">
        <h1 style="color: white; margin-bottom: 0;">🔖 Web Content Manager</h1>
        <p style="color: white; opacity: 0.9; font-size: 1.1rem;">
        Save, organize, and rediscover your web treasures
        </p>
    </div>
    """, unsafe_allow_html=True)

def login_form():
    """
    Display login form with public access option.
    Handles owner, guest, and public modes.
    """
    # Hardcoded passwords
    ADMIN_PASSWORD = "admin123"
    GUEST_PASSWORD = "guest456"
    
    # Dynamic keys for inputs
    if 'password_input_counter' not in st.session_state:
        st.session_state['password_input_counter'] = 0
    if 'username_input_counter' not in st.session_state:
        st.session_state['username_input_counter'] = 0
    
    password_input_key = f"password_input_{st.session_state['password_input_counter']}"
    username_input_key = f"username_input_{st.session_state['username_input_counter']}"
    
    st.markdown("""
    <div class="login-container">
        <h2 class="login-title">🔖 Web Content Manager</h2>
        <p class="login-info">Log in as Owner or Guest, or continue as Public to save links temporarily.</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        with st.form(key="login_form", clear_on_submit=True):
            password = st.text_input(
                "Enter Password",
                type="password",
                help="Enter the password for owner or guest mode",
                key=password_input_key,
                value='',
                autocomplete="off"
            )
            
            username = st.text_input(
                "Enter Username (Guest Mode)",
                placeholder="Your username",
                help="Required for guest mode to access your personal file",
                key=username_input_key,
                value='',
                autocomplete="off"
            )
            
            submitted = st.form_submit_button("🔑 Login")
            
            if submitted:
                logging.debug(f"Login attempt: Password={password}, Username={username}")
                if password == ADMIN_PASSWORD:
                    st.session_state['mode'] = "owner"
                    st.session_state['username'] = None
                    st.session_state['password_input_counter'] += 1
                    st.session_state['username_input_counter'] += 1
                    st.success("✅ Logged in as Owner!")
                    st.rerun()
                elif password == GUEST_PASSWORD:
                    if username:
                        st.session_state['mode'] = "guest"
                        st.session_state['username'] = username
                        st.session_state['password_input_counter'] += 1
                        st.session_state['username_input_counter'] += 1
                        st.success(f"✅ Logged in as Guest: {username}!")
                        st.rerun()
                    else:
                        st.error("Please enter a username for guest mode")
                else:
                    st.error("Invalid password")
                    st.session_state['mode'] = "public"
                    st.session_state['password_input_counter'] += 1
                    st.session_state['username_input_counter'] += 1
                    st.rerun()
    except Exception as e:
        st.error(f"Form error: {str(e)}. Using fallback login.")
        logging.error(f"Form error: {str(e)}")
        # Fallback non-form login
        password = st.text_input(
            "Enter Password (Fallback)",
            type="password",
            key=f"fallback_password_{st.session_state['password_input_counter']}",
            value='',
            autocomplete="off"
        )
        username = st.text_input(
            "Enter Username (Guest Mode, Fallback)",
            placeholder="Your username",
            key=f"fallback_username_{st.session_state['username_input_counter']}",
            value='',
            autocomplete="off"
        )
        if st.button("🔑 Login (Fallback)", key=f"fallback_login_{st.session_state['password_input_counter']}"):
            logging.debug(f"Fallback login attempt: Password={password}, Username={username}")
            if password == ADMIN_PASSWORD:
                st.session_state['mode'] = "owner"
                st.session_state['username'] = None
                st.session_state['password_input_counter'] += 1
                st.session_state['username_input_counter'] += 1
                st.success("✅ Logged in as Owner!")
                st.rerun()
            elif password == GUEST_PASSWORD and username:
                st.session_state['mode'] = "guest"
                st.session_state['username'] = username
                st.session_state['password_input_counter'] += 1
                st.session_state['username_input_counter'] += 1
                st.success(f"✅ Logged in as Guest: {username}!")
                st.rerun()
            elif password == GUEST_PASSWORD:
                st.error("Please enter a username for guest mode")
            else:
                st.session_state['mode'] = "public"
                st.session_state['password_input_counter'] += 1
                st.session_state['username_input_counter'] += 1
                st.rerun()
    
    if st.button("🌐 Continue as Public", key="public_access_button", help="Access without logging in (temporary storage)"):
        st.session_state['mode'] = "public"
        st.session_state['password_input_counter'] += 1
        st.session_state['username_input_counter'] += 1
        st.rerun()

def add_link_section(df, excel_file, mode):
    """
    Section for adding new links with Fetch Metadata button and form.
    
    Args:
        df (DataFrame): DataFrame to add links to
        excel_file (str): Name of the Excel file
        mode (str): 'owner', 'guest', or 'public'
    
    Returns:
        DataFrame: Updated DataFrame
    """
    from utils.data_manager import save_data
    
    st.markdown("### 🌐 Add New Web Content")
    
    # Initialize user DataFrame for public mode
    if mode == "public" and 'user_df' not in st.session_state:
        st.session_state['user_df'] = pd.DataFrame(columns=[
            'id', 'url', 'title', 'description', 'tags', 
            'created_at', 'updated_at'
        ])
    
    # Determine the DataFrame to use
    working_df = st.session_state['user_df'] if mode == "public" else df
    
    # Dynamic key for url_input to force reset
    if 'url_input_counter' not in st.session_state:
        st.session_state['url_input_counter'] = 0
    url_input_key = f"url_input_{st.session_state['url_input_counter']}"
    
    # Clear URL field if signaled
    url_value = '' if st.session_state.get('clear_url', False) else st.session_state.get(url_input_key, '')
    
    # Fetch Metadata button
    url_temp = st.text_input(
        "URL*", 
        value=url_value,
        placeholder="https://example.com",
        key=url_input_key,
        help="Enter the full URL including https://"
    )
    
    is_url_valid = url_temp.startswith(("http://", "https://")) if url_temp else False
    
    if st.button("Fetch Metadata", disabled=not is_url_valid, key="fetch_metadata"):
        with st.spinner("Fetching..."):
            title, description, keywords = fetch_metadata(url_temp)
            st.session_state['auto_title'] = title
            st.session_state['auto_description'] = description
            st.session_state['suggested_tags'] = keywords
            st.session_state['clear_url'] = False
    
    # Form for saving link
    with st.form("add_link_form", clear_on_submit=True):
        url = st.text_input(
            "URL (Confirm)*", 
            value=st.session_state.get(url_input_key, ''),
            key="url_form_input",
            help="Confirm the URL to save"
        )
        
        title = st.text_input(
            "Title*", 
            value=st.session_state.get('auto_title', ''),
            help="Give your link a descriptive title",
            key="title_input"
        )
        
        description = st.text_area(
            "Description", 
            value=st.session_state.get('auto_description', ''),
            height=100,
            help="Add notes about why this link is important",
            key="description_input"
        )
        
        # Get all unique tags from DataFrame
        all_tags = sorted({str(tag).strip() for sublist in working_df['tags'] 
                         for tag in (sublist if isinstance(sublist, list) else []) 
                         if str(tag).strip()})
        suggested_tags = st.session_state.get('suggested_tags', []) + \
                       ['research', 'tutorial', 'news', 'tool', 'inspiration']
        all_tags = sorted(list(set(all_tags + [str(tag).strip() for tag in suggested_tags if str(tag).strip()])))
        
        selected_tags = st.multiselect(
            "Tags",
            options=all_tags,
            default=[],
            help="Select existing tags or add new ones below.",
            key="existing_tags_input"
        )
        
        new_tag = st.text_input(
            "Add New Tag (optional)",
            placeholder="Type a new tag and press Enter",
            help="Enter a new tag to add to the selected tags",
            key="new_tag_input"
        )
        
        tags = selected_tags + ([new_tag.strip()] if new_tag.strip() else [])
        
        submitted = st.form_submit_button("💾 Save Link")
        
        if submitted:
            logging.debug(f"Form submitted: URL={url}, Title={title}, Description={description}, Tags={tags}, Mode={mode}")
            if not url:
                st.error("Please enter a URL")
            elif not title:
                st.error("Please enter a title")
            else:
                working_df, action = save_link(working_df, url, title, description, tags)
                if action:
                    logging.debug(f"Displaying success message and balloons for action: {action}")
                    if mode in ["owner", "guest"]:
                        if save_data(working_df, excel_file):
                            st.session_state['df'] = working_df
                            st.success(f"✅ Link {action} successfully!")
                            st.balloons()
                            time.sleep(0.5)
                            st.session_state['clear_url'] = True
                            st.session_state['url_input_counter'] += 1
                            for key in ['auto_title', 'auto_description', 'suggested_tags']:
                                st.session_state.pop(key, None)
                            st.rerun()
                        else:
                            st.error("Failed to save link to Google Drive")
                    else:
                        st.session_state['user_df'] = working_df
                        st.success(f"✅ Link {action} successfully! Download your links as they are temporary.")
                        st.balloons()
                        time.sleep(0.5)
                        st.session_state['clear_url'] = True
                        st.session_state['url_input_counter'] += 1
                        for key in ['auto_title', 'auto_description', 'suggested_tags']:
                            st.session_state.pop(key, None)
                        st.rerun()
                else:
                    st.error("Failed to process link")
    
    return working_df

def browse_section(df, excel_file, mode):
    """
    Section for browsing and searching saved links.
    
    Args:
        df (DataFrame): DataFrame containing links
        excel_file (str): Name of the Excel file
        mode (str): 'owner', 'guest', or 'public'
    """
    from utils.data_manager import save_data
    
    st.markdown("### 📚 Browse Saved Links")
    
    # Use user_df for public mode
    working_df = st.session_state['user_df'] if mode == "public" else df
    
    if working_df.empty:
        st.info("✨ No links saved yet. Add your first link to get started!")
        return
    
    with st.form("search_form"):
        search_col, tag_col = st.columns([3, 1])
        with search_col:
            search_query = st.text_input(
                "Search content",
                placeholder="Search by title, URL, description, or tags",
                key="search_query",
                help="Enter words to filter links"
            )
        with tag_col:
            all_tags = sorted({str(tag).strip() for sublist in working_df['tags'] 
                             for tag in (sublist if isinstance(sublist, list) else []) 
                             if str(tag).strip()})
            selected_tags = st.multiselect(
                "Filter by tags",
                options=all_tags,
                key="tag_filter",
                help="Select tags to filter links"
            )
        
        submitted = st.form_submit_button("🔍 Search")
    
    filtered_df = working_df.copy()
    
    if search_query or submitted:
        logging.debug(f"Applying search query: {search_query}")
        search_lower = search_query.lower()
        try:
            mask = (
                filtered_df['title'].str.lower().str.contains(search_lower, na=False) |
                filtered_df['url'].str.lower().str.contains(search_lower, na=False) |
                filtered_df['description'].str.lower().str.contains(search_lower, na=False) |
                filtered_df['tags'].apply(
                    lambda x: any(search_lower in str(tag).lower() for tag in (x if isinstance(x, list) else []))
                )
            )
            filtered_df = filtered_df[mask]
            logging.debug(f"Search results: {len(filtered_df)} links found")
        except Exception as e:
            st.error(f"Search error: {str(e)}")
            logging.error(f"Search failed: {str(e)}")
    
    if selected_tags:
        logging.debug(f"Applying tag filter: {selected_tags}")
        try:
            mask = filtered_df['tags'].apply(
                lambda x: any(str(tag) in map(str, (x if isinstance(x, list) else [])) 
                              for tag in selected_tags)
            )
            filtered_df = filtered_df[mask]
            logging.debug(f"Tag filter results: {len(filtered_df)} links found")
        except Exception as e:
            st.error(f"Tag filter error: {str(e)}")
            logging.error(f"Tag filter failed: {str(e)}")
    
    if filtered_df.empty:
        st.warning("No links match your search criteria")
    else:
        st.markdown(f"<small>Found <strong>{len(filtered_df)}</strong> link(s)</small>", unsafe_allow_html=True)
    
    if 'selected_urls' not in st.session_state:
        st.session_state.selected_urls = []

    with st.expander("📊 View All Links as Data Table", expanded=True):
        display_df = filtered_df.copy()
        display_df['tags'] = display_df['tags'].apply(
            lambda x: ', '.join(str(tag) for tag in (x if isinstance(x, list) else [])))
        
        display_df['Select'] = [False] * len(display_df)
        for i, row in display_df.iterrows():
            display_df.at[i, 'Select'] = row['url'] in st.session_state.selected_urls
        
        edited_df = st.data_editor(
            display_df[['Select', 'title', 'url', 'description', 'tags', 'created_at']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Select": st.column_config.CheckboxColumn("Select", help="Select links to delete"),
                "title": "Title",
                "url": st.column_config.LinkColumn("URL"),
                "description": "Description",
                "tags": "Tags",
                "created_at": "Date Added"
            },
            disabled=['title', 'url', 'description', 'tags', 'created_at'],
            key="data_editor"
        )
        
        st.session_state.selected_urls = edited_df[edited_df['Select']]['url'].tolist()
        
        if st.session_state.selected_urls:
            if st.button("🗑️ Delete Selected Links", key="delete_selected"):
                working_df = delete_selected_links(working_df, excel_file, st.session_state.selected_urls, mode)
                if mode == "public":
                    st.session_state['user_df'] = working_df
                else:
                    st.session_state['df'] = working_df
                    save_data(working_df, excel_file)
                st.session_state.selected_urls = []
                st.rerun()

def download_section(df, excel_file, mode):
    """
    Section for downloading saved links as Excel.
    
    Args:
        df (DataFrame): DataFrame containing links
        excel_file (str): Name of the Excel file
        mode (str): 'owner', 'guest', or 'public'
    """
    st.markdown("### 📥 Export Your Links")
    
    # Use user_df for public mode
    working_df = st.session_state['user_df'] if mode == "public" else df
    
    if working_df.empty:
        st.warning("No links available to export")
        return
    
    with st.container():
        st.markdown("""
        <div class="card">
            <h3>Export Options</h3>
            <p>Download your saved links in Excel format</p>
        </div>
        """, unsafe_allow_html=True)
        
        if mode in ["owner", "guest"] and excel_file:
            service = get_drive_service()
            file_id = find_file_in_drive(service, excel_file)
            if file_id:
                output = BytesIO()
                request = service.files().get_media(fileId=file_id)
                downloader = MediaIoBaseDownload(output, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                output.seek(0)
                st.download_button(
                    label=f"Download {mode.capitalize()} Links (Excel)",
                    data=output,
                    file_name=f"{mode}_links.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help=f"Download all {mode} links in Excel format"
                )
        elif mode == "public" and not working_df.empty:
            output = BytesIO()
            working_df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)
            st.download_button(
                label="Download Public Links (Excel)",
                data=output,
                file_name="public_links.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Download all public links in Excel format"
            )
        
        st.markdown(f"""
        <div style="margin-top: 1rem;">
            <p><strong>Stats:</strong> {len(working_df)} links saved | {len(set(tag for sublist in working_df['tags'] for tag in (sublist if isinstance(sublist, list) else [])))} unique tags</p>
        </div>
        """, unsafe_allow_html=True)

def format_tags(tags):
    """
    Format tags as HTML pills for display.
    
    Args:
        tags: List or string of tags
    
    Returns:
        str: HTML string of formatted tags
    """
    if not tags or (isinstance(tags, float) and pd.isna(tags)):
        return ""
    
    if isinstance(tags, str):
        tags = tags.split(',')
    
    html_tags = []
    for tag in tags:
        if tag and str(tag).strip():
            html_tags.append(f"""
            <span class="tag">
                {escape(str(tag).strip())}
            </span>
            """)
    return "".join(html_tags)