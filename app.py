import streamlit as st
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import requests
from pathlib import Path
import re

# Page configuration
st.set_page_config(
    page_title="Slide Manager",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'slides' not in st.session_state:
    st.session_state.slides = []
if 'current_view' not in st.session_state:
    st.session_state.current_view = None
if 'current_slide_id' not in st.session_state:
    st.session_state.current_slide_id = None

# Create data directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DB_FILE = DATA_DIR / "slides.json"

def extract_google_slides_id(url):
    """Extract Google Slides ID from various URL formats"""
    try:
        # Handle different Google Slides URL formats
        
        # Format 1: https://docs.google.com/presentation/d/ID/edit
        if "/d/" in url:
            parts = url.split("/d/")[1].split("/")[0]
            return parts
        
        # Format 2: https://docs.google.com/presentation/d/ID
        if "docs.google.com/presentation/d/" in url:
            pattern = r'docs\.google\.com/presentation/d/([a-zA-Z0-9-_]+)'
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Format 3: Google Drive link that contains presentation ID
        if "drive.google.com" in url:
            # Try to extract from query parameters
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            if 'id' in query_params:
                return query_params['id'][0]
        
        # Format 4: Presentation link
        if "presentation/d/" in url:
            pattern = r'presentation/d/([a-zA-Z0-9-_]+)'
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return url  # Return as-is if no pattern matches
    
    except:
        return url

def extract_title_from_url(url):
    """Try to extract title from URL or use default"""
    try:
        # For Google Slides links, we can't extract title without API
        # So we'll use a default title
        if "docs.google.com" in url or "drive.google.com" in url:
            return "Google Slides Presentation"
        else:
            # For other links, use domain name as title
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            return f"Presentation from {domain}"
    except:
        return "Untitled Presentation"

def load_slides():
    """Load slides from JSON file"""
    try:
        if DB_FILE.exists():
            with open(DB_FILE, 'r') as f:
                st.session_state.slides = json.load(f)
    except:
        st.session_state.slides = []

def save_slides():
    """Save slides to JSON file"""
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(st.session_state.slides, f, indent=2)
    except:
        pass

def get_embed_url(presentation_id):
    """Generate embed URL for Google Slides"""
    return f"https://docs.google.com/presentation/d/{presentation_id}/embed"

def display_slide_card(slide, index):
    """Display a slide card in the dashboard"""
    with st.container():
        # Card header
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### 📊 {slide['title']}")
            st.caption(f"Uploaded by: **{slide['uploader']}** • {slide['date']}")
        
        with col2:
            # Quick stats
            if 'slide_count' in slide:
                st.metric("Slides", slide['slide_count'])
            else:
                st.metric("Type", slide['type'].upper())
        
        # Description
        if slide.get('description'):
            st.markdown(f"**Description:** {slide['description']}")
        
        # Tags
        if slide.get('tags'):
            tags_html = ""
            for tag in slide['tags']:
                tags_html += f'<span style="background-color:#e0f2fe; color:#0369a1; padding:2px 8px; border-radius:12px; margin-right:5px; font-size:0.9em;">{tag}</span>'
            st.markdown(f"**Tags:** {tags_html}", unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("👁️ View", key=f"view_{index}", use_container_width=True):
                st.session_state.current_view = 'view'
                st.session_state.current_slide_id = index
                st.rerun()
        
        with col2:
            if st.button("✏️ Edit", key=f"edit_{index}", use_container_width=True):
                st.session_state.current_view = 'edit'
                st.session_state.current_slide_id = index
                st.rerun()
        
        with col3:
            if st.button("🗑️ Delete", key=f"delete_{index}", type="secondary", use_container_width=True):
                st.session_state.current_view = 'delete'
                st.session_state.current_slide_id = index
                st.rerun()
        
        with col4:
            if slide['type'] == 'google':
                st.link_button("🌐 Update", slide['url'], use_container_width=True)
            else:
                st.link_button("🔗 Update", slide['url'], use_container_width=True)
        
        st.markdown("---")

def display_slide_preview(slide):
    """Display slide preview"""
    st.markdown(f"## 👁️ Preview: {slide['title']}")
    
    # Back button
    if st.button("← Back to Dashboard"):
        st.session_state.current_view = None
        st.session_state.current_slide_id = None
        st.rerun()
    
    st.markdown("---")
    
    # Slide info
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**Uploaded by:** {slide['uploader']}")
        st.markdown(f"**Date:** {slide['date']}")
        st.markdown(f"**Type:** {slide['type'].upper()}")
        
        if slide.get('description'):
            st.markdown("---")
            st.markdown("**Description:**")
            st.info(slide['description'])
    
    with col2:
        if 'slide_count' in slide:
            st.metric("Total Slides", slide['slide_count'])
        else:
            st.metric("Status", "Active")
    
    st.markdown("---")
    
    # Embed the slide
    if slide['type'] == 'google':
        presentation_id = extract_google_slides_id(slide['url'])
        embed_url = get_embed_url(presentation_id)
        
        st.markdown("### 📊 Slide Preview")
        st.info("Note: Make sure the Google Slides has proper sharing permissions (Anyone with the link can view)")
        
        # Embed iframe
        iframe_html = f'''
        <iframe 
            src="{embed_url}" 
            width="100%" 
            height="600" 
            frameborder="0" 
            allowfullscreen="true" 
            mozallowfullscreen="true" 
            webkitallowfullscreen="true">
        </iframe>
        '''
        st.components.v1.html(iframe_html, height=620)
    
    else:
        # For web links
        st.markdown("### 🔗 External Link")
        st.markdown(f"Click here to open: [{slide['url']}]({slide['url']})")

def display_edit_form(slide, index):
    """Display edit form"""
    st.markdown(f"## ✏️ Edit Slide: {slide['title']}")
    
    if st.button("← Back to Dashboard"):
        st.session_state.current_view = None
        st.session_state.current_slide_id = None
        st.rerun()
    
    with st.form(key=f"edit_form_{index}"):
        new_title = st.text_input("Title", value=slide['title'])
        new_description = st.text_area("Description", value=slide.get('description', ''), height=100)
        new_slide_count = st.number_input("Number of Slides", min_value=1, value=slide.get('slide_count', 10))
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Save Changes", use_container_width=True):
                st.session_state.slides[index]['title'] = new_title
                st.session_state.slides[index]['description'] = new_description
                st.session_state.slides[index]['slide_count'] = new_slide_count
                st.session_state.slides[index]['last_modified'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                save_slides()
                st.success("✅ Slide updated successfully!")
                st.session_state.current_view = None
                st.session_state.current_slide_id = None
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Cancel", type="secondary", use_container_width=True):
                st.session_state.current_view = None
                st.session_state.current_slide_id = None
                st.rerun()

def display_delete_confirmation(slide, index):
    """Display delete confirmation"""
    st.markdown(f"## 🗑️ Delete Slide")
    
    if st.button("← Back to Dashboard"):
        st.session_state.current_view = None
        st.session_state.current_slide_id = None
        st.rerun()
    
    st.warning(f"Are you sure you want to delete **'{slide['title']}'**?")
    st.info("This action cannot be undone.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Yes, Delete", type="primary", use_container_width=True):
            st.session_state.slides.pop(index)
            save_slides()
            st.success(f"✅ '{slide['title']}' deleted successfully!")
            st.session_state.current_view = None
            st.session_state.current_slide_id = None
            st.rerun()
    
    with col2:
        if st.button("❌ Cancel", type="secondary", use_container_width=True):
            st.session_state.current_view = None
            st.session_state.current_slide_id = None
            st.rerun()

def main():
    # Load existing slides
    load_slides()
    
    # Sidebar for upload
    with st.sidebar:
        st.title("📤 Upload New Slide")
        
        upload_option = st.radio(
            "Upload Type:",
            ["🌐 Google Drive/Slides", "🔗 Web Link"]
        )
        
        with st.form("upload_form"):
            if upload_option == "🌐 Google Drive/Slides":
                url = st.text_input(
                    "Google Slides Link *",
                    placeholder="https://docs.google.com/presentation/d/...",
                    help="Paste your Google Slides or Google Drive link"
                )
            else:
                url = st.text_input(
                    "Web Link *",
                    placeholder="https://example.com/presentation",
                    help="Paste any web link to your presentation"
                )
            
            title = st.text_input("Slide Title", placeholder="Enter presentation title")
            description = st.text_area("Description", placeholder="Brief description...", height=80)
            uploader = st.text_input("Your Name", placeholder="Enter your name")
            
            if st.form_submit_button("🚀 Upload Slide", type="primary"):
                if not url:
                    st.error("Please enter a URL")
                else:
                    # Extract Google Slides ID if applicable
                    if upload_option == "🌐 Google Drive/Slides":
                        presentation_id = extract_google_slides_id(url)
                        slide_type = 'google'
                    else:
                        presentation_id = url
                        slide_type = 'link'
                    
                    # Use extracted title if none provided
                    final_title = title if title else extract_title_from_url(url)
                    
                    # Create new slide
                    new_slide = {
                        'id': len(st.session_state.slides) + 1,
                        'title': final_title,
                        'url': url,
                        'presentation_id': presentation_id,
                        'type': slide_type,
                        'uploader': uploader or "Anonymous",
                        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'description': description,
                        'last_modified': datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    
                    st.session_state.slides.append(new_slide)
                    save_slides()
                    
                    st.success(f"✅ '{final_title}' uploaded successfully!")
                    st.balloons()
    
    # Main content area
    st.title("📊 Slide Manager")
    
    # Display preview/edit/delete if active
    if st.session_state.current_view == 'view' and st.session_state.current_slide_id is not None:
        slide = st.session_state.slides[st.session_state.current_slide_id]
        display_slide_preview(slide)
        return
    
    elif st.session_state.current_view == 'edit' and st.session_state.current_slide_id is not None:
        slide = st.session_state.slides[st.session_state.current_slide_id]
        display_edit_form(slide, st.session_state.current_slide_id)
        return
    
    elif st.session_state.current_view == 'delete' and st.session_state.current_slide_id is not None:
        slide = st.session_state.slides[st.session_state.current_slide_id]
        display_delete_confirmation(slide, st.session_state.current_slide_id)
        return
    
    # Main dashboard
    st.markdown(f"### You have {len(st.session_state.slides)} presentation(s)")
    
    if not st.session_state.slides:
        st.info("📭 No slides uploaded yet. Use the sidebar to upload your first slide!")
        return
    
   
    
    # Filter slides
    filtered_slides = st.session_state.slides.copy()
   
    
    # Display filtered count
    if filtered_slides:
        st.markdown(f"**Found {len(filtered_slides)} slide(s)**")
        
        # Refresh button
        if st.button("🔄 Refresh Dashboard"):
            load_slides()
            st.rerun()
        
        st.markdown("---")
        
        # Display all slides
        for i, slide in enumerate(filtered_slides):
            # Find original index
            original_index = next((idx for idx, s in enumerate(st.session_state.slides) 
                                 if s['id'] == slide['id']), i)
            display_slide_card(slide, original_index)
    
    else:
        st.info("No slides match your search criteria.")

if __name__ == "__main__":
    main()