import streamlit as st
import requests
import base64
import json
import time
from io import BytesIO
import pandas as pd

# Configure the page
st.set_page_config(
    page_title="Holiday Interest Tagger",
    page_icon="🏖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Lambda function URL
LAMBDA_URL = "https://7cjevxjkw6bxtgwareutls6ymy0zuhqu.lambda-url.ap-southeast-2.on.aws/"

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #4CAF50, #2196F3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    
    .upload-section {
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 2rem 0;
        background-color: #f8f9fa;
    }
    
    .processing-container {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 2rem;
        margin: 2rem 0;
        background-color: #f5f5f5;
        text-align: center;
    }
    
    .success-container {
        border: 1px solid #4CAF50;
        border-radius: 10px;
        padding: 2rem;
        margin: 2rem 0;
        background-color: #e8f5e9;
        text-align: center;
    }
    
    .info-box {
        background-color: #e3f2fd;
        border-left: 5px solid #2196F3;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .feature-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

def encode_file_to_base64(uploaded_file):
    """Convert uploaded file to base64 string."""
    try:
        # Reset file pointer to beginning
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        
        # Debug: Check if we got file content
        if not file_bytes:
            st.error("No file content found. Please try uploading the file again.")
            return None
            
        base64_string = base64.b64encode(file_bytes).decode('utf-8')
        
        # Debug: Show first few characters of base64
        st.write(f"🔍 Debug: Base64 length: {len(base64_string)} characters")
        st.write(f"🔍 Debug: First 50 chars: {base64_string[:50]}...")
        
        return base64_string
    except Exception as e:
        st.error(f"Error encoding file: {str(e)}")
        return None

def call_lambda_function(file_content, file_name, s3_bucket="holiday-interest-test-bucket"):
    """Call the Lambda function to process the file."""
    try:
        # Debug: Validate inputs
        if not file_content:
            st.error("❌ No file content to send!")
            return False, "No file content provided to Lambda function"
        
        payload = {
            "file_content": file_content,
            "file_name": file_name,
            "s3_bucket": s3_bucket
        }
        
        # Debug: Show payload info (without full base64)
        st.write(f"🔍 Debug: Sending file '{file_name}' to bucket '{s3_bucket}'")
        st.write(f"🔍 Debug: Base64 content length: {len(file_content)} chars")
        
        # Show the request being made
        with st.spinner("Sending file to AI processing service..."):
            response = requests.post(
                LAMBDA_URL,
                json=payload,
                timeout=300,  # 5 minute timeout
                headers={'Content-Type': 'application/json'}
            )
        
        # Debug: Show response details
        st.write(f"🔍 Debug: Response status: {response.status_code}")
        st.write(f"🔍 Debug: Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            return True, response.json()
        else:
            # Show the actual error response
            error_text = response.text
            st.error(f"Lambda returned error: {error_text}")
            return False, f"Error: {response.status_code} - {error_text}"
            
    except requests.exceptions.Timeout:
        return False, "Request timed out. The file processing is taking longer than expected."
    except Exception as e:
        st.error(f"Exception in call_lambda_function: {str(e)}")
        return False, f"Network error: {str(e)}"

def download_file_from_url(download_url, filename):
    """Download file from URL and provide download button."""
    try:
        response = requests.get(download_url)
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"Failed to download file: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error downloading file: {str(e)}")
        return None

def main():
    # Header
    st.markdown('<h1 class="main-header">🏖️ Holiday Interest Tagger</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <strong>🤖 AI-Powered Travel Product Enhancement</strong><br>
        Upload your travel products Excel file and our AI will automatically generate engaging summaries 
        and tag each product with relevant holiday interests like "Adventure", "Beach", "Culture & History", and more!
    </div>
    """, unsafe_allow_html=True)

    # Create columns for layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # File upload section
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.markdown("### 📁 Upload Your Products File")
        
        uploaded_file = st.file_uploader(
            "Choose your Excel file (.xlsx)",
            type=['xlsx'],
            help="Upload a .xlsx file containing your travel products data"
        )
        
        if uploaded_file is not None:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            st.info(f"📊 File size: {len(uploaded_file.getvalue())/1024:.1f} KB")
            
            # Show file preview
            try:
                df_preview = pd.read_excel(uploaded_file, nrows=3)
                st.markdown("**📋 File Preview (first 3 rows):**")
                st.dataframe(df_preview, use_container_width=True)
                
                # Reset file pointer for processing
                uploaded_file.seek(0)
            except Exception as e:
                st.warning(f"Could not preview file: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Processing section
        if uploaded_file is not None:
            # Custom S3 bucket option (optional)
            with st.expander("⚙️ Advanced Options (Optional)"):
                s3_bucket = st.text_input(
                    "S3 Bucket Name", 
                    value="holiday-interest-test-bucket",
                    help="Specify a custom S3 bucket for storing results"
                )
            
            # Process button
            if st.button("🚀 Process with AI", type="primary", use_container_width=True):
                # Initialize session state for processing
                if 'processing' not in st.session_state:
                    st.session_state.processing = False
                if 'processed_data' not in st.session_state:
                    st.session_state.processed_data = None
                
                # Start processing
                st.session_state.processing = True
                
                # Convert file to base64
                file_content = encode_file_to_base64(uploaded_file)
                
                if file_content:
                    # Processing animation
                    st.markdown('<div class="processing-container">', unsafe_allow_html=True)
                    st.markdown("### 🤖 AI Processing in Progress...")
                    
                    # Progress bar and status
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Simulate progress updates
                    status_messages = [
                        "📤 Uploading file to processing service...",
                        "🧠 AI analyzing your travel products...",
                        "✍️ Generating engaging product summaries...",
                        "🏷️ Tagging products with holiday interests...",
                        "💾 Preparing your enhanced file..."
                    ]
                    
                    for i, message in enumerate(status_messages):
                        status_text.text(message)
                        progress_bar.progress((i + 1) * 20)
                        time.sleep(1)
                    
                    # Call Lambda function
                    status_text.text("🚀 Processing with Claude AI...")
                    progress_bar.progress(90)
                    
                    success, result = call_lambda_function(
                        file_content, 
                        uploaded_file.name, 
                        s3_bucket if 's3_bucket' in locals() else "holiday-interest-test-bucket"
                    )
                    
                    progress_bar.progress(100)
                    
                    if success:
                        st.session_state.processed_data = result
                        st.session_state.processing = False
                        
                        # Success display
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown('<div class="success-container">', unsafe_allow_html=True)
                        st.markdown("### ✅ Processing Complete!")
                        
                        # Results summary
                        results = result.get('results_summary', {})
                        col_a, col_b, col_c = st.columns(3)
                        
                        with col_a:
                            st.metric("📊 Products Processed", results.get('total_products', 0))
                        with col_b:
                            st.metric("📝 Summaries Generated", results.get('successful_summaries', 0))
                        with col_c:
                            st.metric("🏷️ Products Tagged", results.get('successful_tags', 0))
                        
                        # Download section
                        st.markdown("### 📥 Download Your Enhanced File")
                        
                        download_url = result.get('download_url')
                        if download_url:
                            # Download the file
                            file_data = download_file_from_url(download_url, uploaded_file.name)
                            
                            if file_data:
                                # Create download button
                                enhanced_filename = uploaded_file.name.replace('.xlsx', '_enhanced.xlsx')
                                st.download_button(
                                    label="⬇️ Download Enhanced File",
                                    data=file_data,
                                    file_name=enhanced_filename,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    type="primary",
                                    use_container_width=True
                                )
                                
                                st.success("🎉 Your file has been enhanced with AI-generated summaries and holiday interest tags!")
                                
                                # Show what was added
                                st.info("""
                                **What's been added to your file:**
                                - **Generated Summary**: Engaging 200-300 word descriptions for each product
                                - **Holiday Interest**: 1-3 relevant tags like "Adventure", "Beach", "Culture & History"
                                - **Smart Logic**: Cruise products automatically exclude "Road Trip & Multistop" tags
                                """)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    else:
                        st.session_state.processing = False
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.error(f"❌ Processing failed: {result}")
    
    # Features section
    st.markdown("---")
    st.markdown("### 🌟 Features")
    
    feature_col1, feature_col2, feature_col3 = st.columns(3)
    
    with feature_col1:
        st.markdown("""
        <div class="feature-card">
            <h4>🤖 AI-Powered Summaries</h4>
            <p>Generate engaging, professional product descriptions using Claude AI that highlight key features and attractions.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_col2:
        st.markdown("""
        <div class="feature-card">
            <h4>🏷️ Smart Interest Tagging</h4>
            <p>Automatically categorize products with relevant holiday interests like Adventure, Beach, Culture & History, and more.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_col3:
        st.markdown("""
        <div class="feature-card">
            <h4>🚢 Intelligent Logic</h4>
            <p>Special handling for cruise products, luxury detection, and smart categorization based on product type and content.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: 2rem;">
        <p>🏖️ Holiday Interest Tagger • Powered by Claude AI & AWS Lambda • Built with Streamlit</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()