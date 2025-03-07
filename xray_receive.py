

from pynetdicom import AE, evt, AllStoragePresentationContexts
import os
import requests
from pydicom import dcmread 

# Directory to store received DICOM files
SAVE_DIR = "received_dicom/"
os.makedirs(SAVE_DIR, exist_ok=True)

ALLOWED_AE_TITLES = ["PYNETDICOM"]
ALLOWED_IPS = ["192.168.1.50", "192.168.1.51", "127.0.0.1"]



def handle_store(event):
    print(event.assoc,"event.assoc show")
    requestor_ae = event.assoc.requestor.ae_title
    requestor_ip = event.assoc.requestor.address
    print(requestor_ae,"requestor_ae show")
    print(requestor_ip,"requestor_ip show")
    print(f"Incoming request from AE Title: {requestor_ae}, IP: {requestor_ip}")
    print(f"Received SOP Class UID: {event.dataset.SOPClassUID}")
    
    # Check allowed AE Titles and IPs
    if requestor_ae not in ALLOWED_AE_TITLES or requestor_ip not in ALLOWED_IPS:
        print("Unauthorized request. Rejecting DICOM file.")
        return 0xA801  # Reject request

    # Proceed with file saving
    dataset = event.dataset
    dataset.file_meta = event.file_meta
    file_path = os.path.join(SAVE_DIR, f"{dataset.SOPInstanceUID}.dcm")

    dataset.save_as(file_path, write_like_original=False)
    print(f"Received and saved DICOM file: {file_path}")
    
    upload_dicom(file_path)

    return 0x0000  # Success


# Function to upload DICOM file to backend API
def upload_dicom(file_path):
    
    url = "https://sass-pacs-development.onrender.com/v1/upload_dicom/"
    files = {'dicom_file': open(file_path, 'rb')}


    response = requests.post(url, files=files)
    if response.status_code == 200:
        print("DICOM file uploaded successfully:", response.json())
    else:
        print("Upload failed:", response.text)

# Create the DICOM SCP server
ae = AE(ae_title="STORAGE_SCP")  # Set AE Title for this server
ae.supported_contexts = AllStoragePresentationContexts
handlers = [(evt.EVT_C_STORE, handle_store)]

# Start listening for incoming DICOM images
print("Listening for DICOM images on port 11112...")
ae.start_server(("0.0.0.0", 11112), evt_handlers=handlers, block=True)