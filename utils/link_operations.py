import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import streamlit as st
import logging
import time

def fetch_metadata(url):
    """
    Fetch metadata (title, description, keywords) from a URL.
    
    Args:
        url (str): URL to fetch metadata from
    
    Returns:
        tuple: (title, description, keywords)
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.string if soup.title else url
        description = soup.find('meta', attrs={'name': 'description'})
        description = description['content'] if description else ""
        
        keywords = soup.find('meta', attrs={'name': 'keywords'})
        keywords = keywords['content'].split(',')[:5] if keywords else []
        
        return title, description, [k.strip() for k in keywords if k.strip()]
    except Exception as e:
        st.warning(f"Couldn't fetch metadata: {str(e)}")
        return url, "", []

def save_link(df, url, title, description, tags):
    """
    Save or update a link in the DataFrame.
    
    Args:
        df (DataFrame): DataFrame to save link to
        url (str): URL to save
        title (str): Title of the link
        description (str): Description of the link
        tags (list): List of tags
    
    Returns:
        tuple: (updated DataFrame, action)
    """
    try:
        logging.debug(f"Saving link: URL={url}, Title={title}, Description={description}, Tags={tags}")
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        existing_index = df[df['url'] == url].index
        
        if not existing_index.empty:
            idx = existing_index[0]
            df.at[idx, 'title'] = title
            df.at[idx, 'description'] = description if description else ""
            df.at[idx, 'tags'] = [str(tag).strip() for tag in tags if str(tag).strip()]
            df.at[idx, 'updated_at'] = now
            action = "updated"
        else:
            new_id = df['id'].max() + 1 if not df.empty else 1
            new_entry = {
                'id': new_id,
                'url': url,
                'title': title,
                'description': description if description else "",
                'tags': [str(tag).strip() for tag in tags if str(tag).strip()],
                'created_at': now,
                'updated_at': now
            }
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            action = "saved"
        
        logging.info(f"Link {action} successfully")
        return df, action
    except Exception as e:
        st.error(f"Error saving link: {str(e)}")
        logging.error(f"Link save failed: {str(e)}")
        return df, None

def delete_selected_links(df, excel_file, selected_urls, mode):
    """
    Delete selected links from the DataFrame and update Google Drive.
    
    Args:
        df (DataFrame): DataFrame containing links
        excel_file (str): Name of the Excel file
        selected_urls (list): List of URLs to delete
        mode (str): 'owner', 'guest', or 'public'
    
    Returns:
        DataFrame: Updated DataFrame
    """
    from utils.data_manager import save_data
    
    try:
        logging.debug(f"Deleting URLs: {selected_urls}")
        if not selected_urls:
            st.warning("No links selected for deletion")
            return df
        df = df[~df['url'].isin(selected_urls)]
        if mode in ["owner", "guest"]:
            if save_data(df, excel_file):
                st.session_state['df'] = df
                st.success(f"✅ {len(selected_urls)} link(s) deleted successfully!")
                st.balloons()
                time.sleep(0.5)
            else:
                st.error("Failed to save changes after deletion")
        else:
            st.session_state['user_df'] = df
            st.success(f"✅ {len(selected_urls)} link(s) deleted successfully!")
            st.balloons()
            time.sleep(0.5)
        return df
    except Exception as e:
        st.error(f"Error deleting links: {str(e)}")
        logging.error(f"Delete links failed: {str(e)}")
        return df