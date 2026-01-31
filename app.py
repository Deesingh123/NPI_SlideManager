import streamlit as st
import json
import time
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import re

# Page configuration
st.set_page_config(
    page_title="NPI Manager",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'slides' not in st.session_state:
    st.session_state.slides = []
if 'edit_slide_id' not in st.session_state:
    st.session_state.edit_slide_id = None
if 'delete_slide_id' not in st.session_state:
    st.session_state.delete_slide_id = None
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = 10
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if 'file_last_modified' not in st.session_state:
    st.session_state.file_last_modified = 0
if 'last_checked' not in st.session_state:
    st.session_state.last_checked = datetime.now()
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False
if 'upload_form_data' not in st.session_state:
    st.session_state.upload_form_data = {
        'url': '',
        'title': '',
        'description': '',
        'uploader': ''
    }

# Create data directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DB_FILE = DATA_DIR / "slides.json"

def extract_google_slides_id(url):
    """Extract Google Slides ID from various URL formats"""
    try:
        if "/d/" in url:
            parts = url.split("/d/")[1].split("/")[0]
            return parts
        if "docs.google.com/presentation/d/" in url:
            pattern = r'docs\.google\.com/presentation/d/([a-zA-Z0-9-_]+)'
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        if "drive.google.com" in url:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            if 'id' in query_params:
                return query_params['id'][0]
        if "presentation/d/" in url:
            pattern = r'presentation/d/([a-zA-Z0-9-_]+)'
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return url
    except:
        return url

def is_embeddable_url(url):
    """Check if a web link can be embedded"""
    embeddable_platforms = [
        'canva.com', 'slideshare.net', 'speakerdeck.com', 
        'visme.co', 'prezi.com', 'haikudeck.com', 'slideonline.com'
    ]
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    return any(platform in domain for platform in embeddable_platforms)

def get_embed_code(url):
    """Get embed code for various presentation platforms"""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    if 'canva.com' in domain:
        return f"""
        <iframe 
            src="{url}/embed" 
            width="100%" 
            height="500" 
            frameborder="0" 
            allowfullscreen
            style="border-radius: 8px;">
        </iframe>
        """
    elif 'slideshare.net' in domain:
        match = re.search(r'slideshare\.net/.*/([^/?]+)', url)
        if match:
            slide_id = match.group(1)
            return f"""
            <iframe 
                src="https://www.slideshare.net/slideshow/embed_code/key/{slide_id}" 
                width="100%" 
                height="500" 
                frameborder="0" 
                marginwidth="0" 
                marginheight="0" 
                scrolling="no" 
                allowfullscreen
                style="border-radius: 8px;">
            </iframe>
            """
    elif 'speakerdeck.com' in domain:
        return f"""
        <iframe 
            src="{url}/embed" 
            width="100%" 
            height="500" 
            frameborder="0" 
            allowfullscreen
            style="border-radius: 8px;">
        </iframe>
        """
    
    return None

def extract_title_from_url(url):
    """Try to extract title from URL or use default"""
    try:
        if "docs.google.com" in url or "drive.google.com" in url:
            return "Google Slides Presentation"
        else:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            if 'canva.com' in domain:
                return "Canva Presentation"
            elif 'slideshare.net' in domain:
                return "SlideShare Presentation"
            elif 'speakerdeck.com' in domain:
                return "SpeakerDeck Presentation"
            return f"Presentation from {domain}"
    except:
        return "Untitled Presentation"

def load_slides():
    """Load slides from JSON file"""
    try:
        if DB_FILE.exists():
            with open(DB_FILE, 'r') as f:
                st.session_state.slides = json.load(f)
                # Update file modification time
                st.session_state.file_last_modified = os.path.getmtime(DB_FILE)
                st.session_state.last_refresh = datetime.now()
    except Exception as e:
        st.session_state.slides = []

def save_slides():
    """Save slides to JSON file with timestamp update"""
    try:
        # Mark that we're saving (for preventing self-triggered reloads)
        st.session_state.saving = True
        
        with open(DB_FILE, 'w') as f:
            json.dump(st.session_state.slides, f, indent=2)
        
        # Update file modification time
        st.session_state.file_last_modified = os.path.getmtime(DB_FILE)
        st.session_state.last_refresh = datetime.now()
        
        # Clear saving flag
        time.sleep(0.1)  # Small delay to ensure file is written
        st.session_state.saving = False
        
        return True
    except Exception as e:
        st.error(f"Error saving slides: {e}")
        return False

def get_embed_url(presentation_id):
    """Generate embed URL for Google Slides"""
    return f"https://docs.google.com/presentation/d/{presentation_id}/embed"

def check_for_updates():
    """Check if the slides file has been modified by another user/instance"""
    try:
        if DB_FILE.exists():
            current_mod_time = os.path.getmtime(DB_FILE)
            
            # If file was modified by another instance (not by us)
            if (current_mod_time > st.session_state.file_last_modified and 
                not st.session_state.get('saving', False)):
                
                # Load the updated slides
                with open(DB_FILE, 'r') as f:
                    updated_slides = json.load(f)
                
                # Only update if slides are different
                if updated_slides != st.session_state.slides:
                    st.session_state.slides = updated_slides
                    st.session_state.file_last_modified = current_mod_time
                    st.session_state.last_refresh = datetime.now()
                    st.session_state.last_checked = datetime.now()
                    return True
                
                st.session_state.file_last_modified = current_mod_time
                st.session_state.last_checked = datetime.now()
        
        return False
    except Exception as e:
        return False

def display_slide_in_dashboard(slide, index):
    """Display a slide directly in the dashboard"""
    with st.container():
        st.markdown(f"""
        <div style="
            background: #ffffff;
            border-radius: 8px 8px 0 0;
            padding: 20px;
            margin: 15px 0 0 0;
            border: 1px solid #e0e0e0;
            border-bottom: none;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 1.4rem; font-weight: 600;">
                        📊 {slide['title']}
                    </h3>
                    <div style="display: flex; align-items: center; gap: 15px; color: #666; font-size: 0.9em;">
                        <span style="display: flex; align-items: center; gap: 5px;">
                            👤 {slide['uploader']}
                        </span>
                        <span>•</span>
                        <span>{slide['date']}</span>
                        <span>•</span>
                        <span title="Last modified" style="color: #888;">
                            📝 {slide.get('last_modified', slide['date'])}
                        </span>
                    </div>
                </div>
                <div style="
                    background: {'#e8f4fd' if slide['type'] == 'google' else '#f0f0f0'};
                    color: {'#1a73e8' if slide['type'] == 'google' else '#666'};
                    padding: 6px 12px;
                    border-radius: 15px;
                    font-size: 0.9em;
                    font-weight: 500;
                ">
                    {'Google Slides' if slide['type'] == 'google' else 'Web Link'}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if slide.get('description'):
            st.markdown(f"""
            <div style="
                background: #f8f9fa;
                padding: 15px 20px;
                border-left: 3px solid #1a73e8;
                margin: 0;
                border-right: 1px solid #e0e0e0;
                border-bottom: 1px solid #e0e0e0;
            ">
                <p style="margin: 0; color: #555; font-size: 1em; line-height: 1.5;">{slide['description']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="
            background: #ffffff;
            padding: 0;
            border: 1px solid #e0e0e0;
            border-top: none;
            border-radius: 0 0 8px 8px;
        ">
        """, unsafe_allow_html=True)
        
        if slide['type'] == 'google':
            presentation_id = extract_google_slides_id(slide['url'])
            embed_url = get_embed_url(presentation_id)
            
            iframe_html = f'''
            <iframe 
                src="{embed_url}" 
                width="100%" 
                height="450" 
                frameborder="0" 
                allowfullscreen="true" 
                mozallowfullscreen="true" 
                webkitallowfullscreen="true"
                style="border-radius: 0;">
            </iframe>
            '''
            st.components.v1.html(iframe_html, height=470)
            
            st.markdown(f"""
            <div style="
                padding: 15px;
                background: #f8f9fa;
                border-top: 1px solid #e0e0e0;
                text-align: center;
            ">
                <a href="{slide['url']}" target="_blank" style="
                    text-decoration: none;
                    color: #1a73e8;
                    font-size: 0.95em;
                    padding: 8px 20px;
                    border: 1px solid #1a73e8;
                    border-radius: 4px;
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    background: white;
                ">
                    🔗 Open in Google Slides
                </a>
            </div>
            """, unsafe_allow_html=True)
        
        else:
            embed_code = get_embed_code(slide['url'])
            
            if embed_code and is_embeddable_url(slide['url']):
                st.components.v1.html(embed_code, height=520)
                st.markdown(f"""
                <div style="
                    padding: 15px;
                    background: #f8f9fa;
                    border-top: 1px solid #e0e0e0;
                    text-align: center;
                ">
                    <a href="{slide['url']}" target="_blank" style="
                        text-decoration: none;
                        color: #1a73e8;
                        font-size: 0.95em;
                        padding: 8px 20px;
                        border: 1px solid #1a73e8;
                        border-radius: 4px;
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        background: white;
                    ">
                        🔗 Open Original
                    </a>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="
                    padding: 40px 20px;
                    background: #f8f9fa;
                    text-align: center;
                ">
                    <div style="font-size: 3rem; margin-bottom: 15px; color: #666;">🔗</div>
                    <h4 style="color: #2c3e50; margin-bottom: 10px;">External Presentation</h4>
                    <p style="color: #666; margin-bottom: 20px; font-size: 0.95em;">
                        {slide['url'][:80]}{'...' if len(slide['url']) > 80 else ''}
                    </p>
                    <a href="{slide['url']}" target="_blank" style="
                        text-decoration: none;
                        background: #1a73e8;
                        color: white;
                        padding: 10px 25px;
                        border-radius: 4px;
                        font-weight: 500;
                        display: inline-block;
                    ">
                        Open Presentation
                    </a>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"✏️ Edit", key=f"edit_{index}_{slide['id']}", use_container_width=True):
                st.session_state.edit_slide_id = index
                st.rerun()
        
        with col2:
            if st.button(f"🔄 Update", key=f"update_{index}_{slide['id']}", use_container_width=True):
                st.session_state.slides[index]['last_modified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_slides()
                st.success("Slide updated!")
                time.sleep(0.5)
                st.rerun()
        
        with col3:
            if st.button(f"🗑️ Delete", key=f"delete_{index}_{slide['id']}", type="secondary", use_container_width=True):
                st.session_state.delete_slide_id = index
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)

def display_edit_form(slide, index):
    """Display edit form"""
    st.markdown(f"## ✏️ Edit Slide: {slide['title']}")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("← Back to Dashboard", use_container_width=True):
            st.session_state.edit_slide_id = None
            st.rerun()
    
    with st.form(key=f"edit_form_{index}_{slide['id']}"):
        new_title = st.text_input("Title", value=slide['title'])
        new_description = st.text_area("Description", value=slide.get('description', ''), height=100)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Save Changes", use_container_width=True):
                st.session_state.slides[index]['title'] = new_title
                st.session_state.slides[index]['description'] = new_description
                st.session_state.slides[index]['last_modified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_slides()
                st.success("Slide updated successfully!")
                time.sleep(0.5)
                st.session_state.edit_slide_id = None
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Cancel", type="secondary", use_container_width=True):
                st.session_state.edit_slide_id = None
                st.rerun()

def display_delete_confirmation(slide, index):
    """Display delete confirmation"""
    st.markdown(f"## 🗑️ Delete Slide")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("← Back to Dashboard", use_container_width=True):
            st.session_state.delete_slide_id = None
            st.rerun()
    
    st.markdown(f"""
    <div style="
        background: #fff8e1;
        border: 1px solid #ffecb3;
        border-radius: 8px;
        padding: 25px;
        text-align: center;
        margin: 20px 0;
    ">
        <div style="font-size: 2.5rem; margin-bottom: 15px;">⚠️</div>
        <h3 style="color: #ff6f00; margin-bottom: 15px;">
            Delete "{slide['title']}"?
        </h3>
        <p style="color: #666;">
            This action cannot be undone. The slide will be permanently removed.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Yes, Delete", type="primary", use_container_width=True):
            st.session_state.slides.pop(index)
            save_slides()
            st.success(f"'{slide['title']}' deleted successfully!")
            time.sleep(0.5)
            st.session_state.delete_slide_id = None
            st.rerun()
    
    with col2:
        if st.button("❌ Cancel", type="secondary", use_container_width=True):
            st.session_state.delete_slide_id = None
            st.rerun()

def handle_upload(upload_option, url, title, description, uploader):
    """Handle slide upload with proper state management"""
    if not url:
        st.error("Please enter a URL")
        return False
    
    if upload_option == "🌐 Google Drive/Slides":
        presentation_id = extract_google_slides_id(url)
        slide_type = 'google'
    else:
        presentation_id = url
        slide_type = 'link'
    
    final_title = title if title else extract_title_from_url(url)
    
    new_slide = {
        'id': len(st.session_state.slides) + 1,
        'title': final_title,
        'url': url,
        'presentation_id': presentation_id,
        'type': slide_type,
        'uploader': uploader or "Anonymous",
        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'description': description,
        'last_modified': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    st.session_state.slides.append(new_slide)
    save_slides()
    
    # Reset form data
    st.session_state.upload_form_data = {
        'url': '',
        'title': '',
        'description': '',
        'uploader': ''
    }
    
    return True

def main():
    # Load existing slides
    load_slides()
    
    # Sidebar for upload
    with st.sidebar:
        st.markdown("""
        <div style="
            background: #1a73e8;
            color: white;
            padding: 20px;
            border-radius: 0;
            margin: -20px -20px 20px -20px;
        ">
            <h2 style="margin: 0; color: white; font-size: 1.5rem;">📤 Upload New Slide</h2>
            <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 0.9em;">
                Share presentations with your team
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        upload_option = st.radio(
            "Upload Type:",
            ["🌐 Google Drive/Slides", "🔗 Web Link"],
            label_visibility="collapsed",
            key="upload_option"
        )
        
        # Use session state for form persistence
        if 'upload_form' not in st.session_state:
            st.session_state.upload_form = {
                'url': '',
                'title': '',
                'description': '',
                'uploader': ''
            }
        
        # Create form with unique key
        form_key = f"upload_form_{len(st.session_state.slides)}"
        with st.form(key=form_key, clear_on_submit=True):
            st.markdown("**URL**")
            if upload_option == "🌐 Google Drive/Slides":
                url = st.text_input(
                    "Google Slides Link",
                    value=st.session_state.upload_form['url'],
                    placeholder="https://docs.google.com/presentation/d/...",
                    help="Paste your Google Slides or Google Drive link",
                    label_visibility="collapsed",
                    key=f"url_input_{form_key}"
                )
            else:
                url = st.text_input(
                    "Web Link",
                    value=st.session_state.upload_form['url'],
                    placeholder="https://example.com/presentation",
                    help="Supported: Canva, SlideShare, SpeakerDeck, etc.",
                    label_visibility="collapsed",
                    key=f"url_input_{form_key}"
                )
            
            st.markdown("**Title**")
            title = st.text_input(
                "Slide Title",
                value=st.session_state.upload_form['title'],
                placeholder="Enter presentation title",
                label_visibility="collapsed",
                key=f"title_input_{form_key}"
            )
            
            st.markdown("**Description**")
            description = st.text_area(
                "Description",
                value=st.session_state.upload_form['description'],
                placeholder="Brief description...",
                height=80,
                label_visibility="collapsed",
                key=f"desc_input_{form_key}"
            )
            
            st.markdown("**Your Name**")
            uploader = st.text_input(
                "Your Name",
                value=st.session_state.upload_form['uploader'],
                placeholder="Enter your name",
                label_visibility="collapsed",
                key=f"uploader_input_{form_key}"
            )
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                submit_button = st.form_submit_button(
                    "🚀 Upload Slide", 
                    use_container_width=True,
                    type="primary"
                )
            
            with col2:
                clear_button = st.form_submit_button(
                    "Clear", 
                    type="secondary", 
                    use_container_width=True
                )
            
            # Handle form submission
            if submit_button and not st.session_state.get('form_submitted', False):
                # Set flag to prevent multiple submissions
                st.session_state.form_submitted = True
                
                success = handle_upload(upload_option, url, title, description, uploader)
                if success:
                    # Store form data in session state
                    st.session_state.upload_form = {
                        'url': url,
                        'title': title,
                        'description': description,
                        'uploader': uploader
                    }
                    st.success(f"'{title if title else extract_title_from_url(url)}' uploaded successfully!")
                    st.balloons()
                    # Reset form data for next use
                    st.session_state.upload_form = {
                        'url': '',
                        'title': '',
                        'description': '',
                        'uploader': ''
                    }
                    # Clear submission flag after delay
                    time.sleep(0.5)
                    st.session_state.form_submitted = False
                    st.rerun()
            
            if clear_button:
                # Clear form data
                st.session_state.upload_form = {
                    'url': '',
                    'title': '',
                    'description': '',
                    'uploader': ''
                }
                st.rerun()
        
        # Auto-refresh settings in sidebar
        st.markdown("---")
        st.markdown("### 🔄 Refresh Settings")
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox(
            "Enable auto-refresh", 
            value=st.session_state.auto_refresh,
            help="Automatically check for updates from other users"
        )
        
        if auto_refresh != st.session_state.auto_refresh:
            st.session_state.auto_refresh = auto_refresh
            st.rerun()
        
        if st.session_state.auto_refresh:
            refresh_interval = st.select_slider(
                "Check every",
                options=[5, 10, 15, 30, 60],
                value=st.session_state.refresh_interval,
                format_func=lambda x: f"{x} seconds" if x < 60 else "1 minute"
            )
            
            if refresh_interval != st.session_state.refresh_interval:
                st.session_state.refresh_interval = refresh_interval
                st.rerun()
        
        # Manual refresh button
        if st.button("🔄 Check for Updates Now", use_container_width=True, key="check_updates_btn"):
            if check_for_updates():
                st.success("Slides updated!")
            else:
                st.info("No new updates found.")
            time.sleep(1)
            st.rerun()
        
        # Last checked time
        if st.session_state.get('last_checked'):
            st.caption(f"Last checked: {st.session_state.last_checked.strftime('%H:%M:%S')}")
    
    # Main content area with PAdGET branding
    st.markdown("""
    <style>
    .header-container {
       display: flex;
       align-items: center;
       height: 180px;
       justify-content: space-between;
       padding: 10px 20px;
       border-radius: 14px;
       background: linear-gradient(135deg, #f8fafc, #eef2ff);
       box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
       transition: all 0.3s ease;
       margin-bottom: 10px;
    }

    .header-container:hover {
      transform: translateY(-2px);
      box-shadow: 0 14px 32px rgba(0, 0, 0, 0.15);
    }

    .header-title {
      font-size: 3.7rem;
      font-weight: 700;
      color: #1a73e8;
      margin: 0;
      letter-spacing: 2px;
      shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
    }

    .header-subtitle {
       font-size: 1.0rem;
       color: #475569;
    }

    .logo-img {
       height: 100px;
       padding: 10px;
       border-radius: 12px;
    }
    
    .refresh-status {
        padding: 5px 10px;
        background: #f0f9ff;
        border-radius: 12px;
        font-size: 0.85em;
        color: #0369a1;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }
    </style>

    <div class="header-container">
      <img
        src="https://www.sentinel-technologies.net/assets/customer_logos/padget.jpg"
        class="logo-img"
        alt="PAdGET Logo"
      />

      <div style="text-align: right;">
        <div class="header-title">PROJECT 4M READINESS REVIEW</div>
        <div class="header-subtitle">
            All team presentations in one place
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    
    # Show edit form if editing
    if st.session_state.edit_slide_id is not None:
        slide = st.session_state.slides[st.session_state.edit_slide_id]
        display_edit_form(slide, st.session_state.edit_slide_id)
        return
    
    # Show delete confirmation if deleting
    if st.session_state.delete_slide_id is not None:
        slide = st.session_state.slides[st.session_state.delete_slide_id]
        display_delete_confirmation(slide, st.session_state.delete_slide_id)
        return
    
    # Auto-refresh logic - ONLY if we're not in the middle of a form submission
    if st.session_state.auto_refresh and not st.session_state.get('form_submitted', False):
        current_time = datetime.now()
        time_since_last_check = (current_time - st.session_state.last_checked).total_seconds()
        
        if time_since_last_check >= st.session_state.refresh_interval:
            if check_for_updates():
                # Show a subtle notification that updates were loaded
                update_container = st.empty()
                with update_container:
                    st.info(f"🔄 Auto-refresh: Loaded updates at {current_time.strftime('%H:%M:%S')}")
                    time.sleep(1.5)
                update_container.empty()
            else:
                st.session_state.last_checked = current_time
    
    # Dashboard stats and refresh status
    total_slides = len(st.session_state.slides)
    google_slides = len([s for s in st.session_state.slides if s['type'] == 'google'])
    web_links = len([s for s in st.session_state.slides if s['type'] == 'link'])
    
    # Refresh status header
    col_header1, col_header2 = st.columns([3, 1])
    
    with col_header1:
        st.markdown(f"### 📊 Team Presentations ({total_slides} total)")
    
    with col_header2:
        refresh_status = ""
        if st.session_state.auto_refresh:
            refresh_status = f"🔄 Auto-refresh: Every {st.session_state.refresh_interval}s"
        else:
            refresh_status = "⏸️ Auto-refresh: Off"
        
        st.markdown(f"""
        <div style="text-align: right; margin-bottom: 10px;">
            <span class="refresh-status">{refresh_status}</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Stats cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            text-align: center;
        ">
            <div style="font-size: 1.8rem; margin-bottom: 10px; color: #2c3e50;">📊</div>
            <div style="font-size: 1.8rem; font-weight: bold; color: #2c3e50;">{total_slides}</div>
            <div style="color: #666; font-size: 0.9em; margin-top: 5px;">Total Slides</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            text-align: center;
        ">
            <div style="font-size: 1.8rem; margin-bottom: 10px; color: #2c3e50;">🌐</div>
            <div style="font-size: 1.8rem; font-weight: bold; color: #2c3e50;">{google_slides}</div>
            <div style="color: #666; font-size: 0.9em; margin-top: 5px;">Google Slides</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            text-align: center;
        ">
            <div style="font-size: 1.8rem; margin-bottom: 10px; color: #2c3e50;">🔗</div>
            <div style="font-size: 1.8rem; font-weight: bold; color: #2c3e50;">{web_links}</div>
            <div style="color: #666; font-size: 0.9em; margin-top: 5px;">Web Links</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        if st.button("🔄 Force Refresh", use_container_width=True, key="force_refresh_main"):
            if check_for_updates():
                st.success("Slides refreshed!")
            else:
                st.info("No updates found.")
            time.sleep(1)
            st.rerun()
    
    # Last updated info
    if DB_FILE.exists():
        try:
            mod_time = datetime.fromtimestamp(os.path.getmtime(DB_FILE))
            st.caption(f"📝 Last database update: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            pass
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main dashboard content
    if not st.session_state.slides:
        st.markdown("""
        <div style="
            background: white;
            padding: 40px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #e0e0e0;
            margin: 20px 0;
        ">
            <div style="font-size: 3.5rem; margin-bottom: 20px; color: #ddd;">📭</div>
            <h3 style="color: #2c3e50; margin-bottom: 15px;">No slides uploaded yet</h3>
            <p style="color: #666; max-width: 500px; margin: 0 auto 25px auto;">
                Get started by uploading your first presentation using the sidebar form.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Auto-refresh placeholder if no slides
        if st.session_state.auto_refresh and not st.session_state.get('form_submitted', False):
            time.sleep(st.session_state.refresh_interval)
            st.rerun()
        
        return
    
    # Display all slides
    for i, slide in enumerate(st.session_state.slides):
        display_slide_in_dashboard(slide, i)
    
    # Final auto-refresh trigger at the end - ONLY if not in form submission
    if st.session_state.auto_refresh and not st.session_state.get('form_submitted', False):
        current_time = datetime.now()
        time_since_last_check = (current_time - st.session_state.last_checked).total_seconds()
        
        if time_since_last_check >= st.session_state.refresh_interval:
            # Create a placeholder for the next refresh
            refresh_placeholder = st.empty()
            with refresh_placeholder:
                st.caption(f"🔄 Next auto-refresh in {st.session_state.refresh_interval - time_since_last_check:.0f}s")
            
            # Small delay before checking again
            time.sleep(0.1)
            st.rerun()

if __name__ == "__main__":
    main()
