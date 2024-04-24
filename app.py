# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 15:38:25 2024

@author: P00121384
"""
###############################################################################
### Importing Dependencies
from PIL import Image
import yaml, base64, os
from pathlib import Path as p
from collections import defaultdict
from datetime import datetime
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
from google.cloud import storage
###############################################################################
### Initializing Directory
data_folder = p.cwd() / "temp_files"
p(data_folder).mkdir(parents=True, exist_ok=True)
PROJECT_ID = os.environ.get("GCP_PROJECT")  # Your Google Cloud Project ID
LOCATION = os.environ.get("GCP_REGION")  # Your Google Cloud Project Region
###############################################################################
@st.cache_data
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data=f.read()
    return base64.b64encode(data).decode()
###############################################################################
def download_bucket_contents(bucket_name, local_dir):
    """Downloads all files from a GCP bucket to a local folder with the same structure.
    Args:
        bucket_name (str): The name of the GCP bucket to download from.
        local_dir (str): The local directory to download the files to.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    for blob in bucket.list_blobs(prefix="output/"):
        blob_name = blob.name
        # Create the corresponding local directory structure
        local_path = os.path.join(local_dir, blob_name)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)  # Create directories if needed
        # Download the blob to the local path
        blob.download_to_filename(local_path)
###############################################################################
def get_image_paths(folder_path, extensions=[".png"]):
      """
      Gets all the names of image files with specified extensions in a folder.
      Args:
          folder_path: The path to the folder.
          extensions: A list of image file extensions (defaults to png, jpg, jpeg).
      Returns:
          A list containing the names of all image files in the folder with matching extensions.
      """
      filenames = os.listdir(folder_path)
      image_paths = [filename for filename in filenames if any(filename.endswith(ext) for ext in extensions)]
      return image_paths
###############################################################################
def convert_dt(time_stamp):
    # Extract year, month, day, hour, minute, second from the timestamp string
    year = int(time_stamp[:4])
    month = int(time_stamp[4:6])
    day = int(time_stamp[6:8])
    hour = int(time_stamp[8:10])
    minute = int(time_stamp[10:12])
    second = int(time_stamp[12:14])
    # Create datetime object
    dt = datetime(year, month, day, hour, minute, second)
    # Print the datetime in the desired format
    return dt.strftime("%Y-%m-%d %H:%M:%S")
###############################################################################
### Main Function
def main_func():
    ########################## Background Image #################################
    img = get_img_as_base64("./streamlit/background.jpg")
    img_1 = get_img_as_base64("./streamlit/sidebar.jpg")
    page_bg_img = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
    background-image: url("data:image/png;base64,{img}");
    background-size: cover;
    }}
    [data-testid="stHeader"] {{
    background-color: rgba(0,0,0,0);   
    }}
    [data-testid="stToolbar"] {{
    right: 2rem;
    }}
    [data-testid="stSidebar"] {{
    background-image: url("data:image/png;base64,{img_1}");
    background-size: cover;
    }}
    </style>
    """
    ######################### Download the Data ###############################
    # Replace with your GCP bucket name
    bucket_name = "apac-hack-bucket"
    # Replace with your desired local directory (create it if necessary)
    local_dir = "temp_files"
    download_bucket_contents(bucket_name, local_dir)
    ###################### List unique customers ##############################
    customer_list_display = []
    customer_list = []
    for file in os.listdir('temp_files/output'):
        customer_list_display.append(str(file).split("_")[0])
        customer_list.append(str(file))
    customer_list_display = list(set(customer_list_display))
    ################ Get the multiple occurence of customer ###################
    d = defaultdict(list)
    for item in customer_list:
      key, value = item.split('_')
      d[key].append(convert_dt(str(int(value))))
    # Convert defaultdict to a regular dictionary
    result = dict(d)
    ########################## Set Page Title #################################
    with st.sidebar:
        st.image("./streamlit/title_image.jpg", width=100)
        st.title("Bespoke Haven - Customer Insights")
        option = st.selectbox('Select the Customer:', customer_list_display)
        # Further multiple occurence filter
        if option:
          sub_category_options = result[str(option)]
          sub_category_filter = st.selectbox("Select the Journey:", sub_category_options)
    ########################## Main display ###################################
    st.markdown(page_bg_img, unsafe_allow_html=True)
    st.markdown("---")
    ########################## Display Text ###################################
    dt = datetime.strptime(sub_category_filter, "%Y-%m-%d %H:%M:%S")
    formatted_str = dt.strftime("%Y%m%d%H%M%S")
    #sub_folder = [item for item in customer_list if item.startswith(option)][0]
    sub_folder = str(option)+"_"+str(formatted_str)
    folder_path = 'temp_files/output/'+sub_folder    
    text_paths = folder_path + "/" + "agent_content.txt"
    # Replace "path/to/your/file.txt" with the actual path to your file on server
    with open(text_paths, "r") as f:
        text = f.read()
    st.write(text)
###############################################################################
### Run the application
if __name__ == "__main__":
    ########################## Page configuration #############################
    image = Image.open('./streamlit/title_image.jpg')
    st.set_page_config(
        page_title="Bespoke Haven",
        page_icon=image,
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'About': "#### Agent UI showing the details of customer journey and customized AI generated specific images and insights\n **Contact for updates** : updates@bespokehaven.com"
        })    
    ############################# Aunthentication #############################
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )    
    authenticator.login()
    ############################ Main Function ################################
    if st.session_state["authentication_status"]:
        authenticator.logout('Logout', 'main', key='unique_key')
        st.write(f'Welcome *{st.session_state["name"]}*')
        main_func()
    elif st.session_state["authentication_status"] is False:
        st.error('Username/password is incorrect')
    elif st.session_state["authentication_status"] is None:
        st.warning('Please enter your username and password')
###############################################################################
