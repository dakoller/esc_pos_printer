from escpos.printer import Network, Dummy
import requests
import json
import tempfile
import os
import re
from io import BytesIO
from urllib.parse import urlparse

# Configuration URLs - make these configurable
SOURCE_WEBHOOK_URL = 'https://automation.tools.palino.me/webhook/dee40ef0-34c6-42d5-92c5-e9701b82e49d'
CALLBACK_WEBHOOK_URL = 'https://automation.tools.palino.me/webhook/1352fcf6-6157-49c8-8a45-542af9c08b90'

# Printer setup
printer_ip = '192.168.2.134'
p = Network(printer_ip, timeout=30)

# Fetch the webpage content
try:
    response = requests.get(SOURCE_WEBHOOK_URL)
    response.raise_for_status()  # Raise exception for HTTP errors
    
    print("Response content:")
    print(response.text)
    
    # Parse JSON content
    data = json.loads(response.text)
    
    # Extract image links and transaction IDs
    image_links = []
    client_transaction_ids = []
    
    # Check if data is a list
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                # Process href links
                if "href" in item:
                    if isinstance(item["href"], list):
                        image_links.extend(item["href"])
                    elif isinstance(item["href"], str):
                        image_links.append(item["href"])
                
                # Process client transaction IDs if they're in the JSON
                if "client_transaction_id" in item:
                    if isinstance(item["client_transaction_id"], list):
                        client_transaction_ids.extend(item["client_transaction_id"])
                    elif isinstance(item["client_transaction_id"], str):
                        client_transaction_ids.append(item["client_transaction_id"])
    # If data is a dictionary
    elif isinstance(data, dict):
        # Process href links
        if "href" in data:
            if isinstance(data["href"], list):
                image_links.extend(data["href"])
            elif isinstance(data["href"], str):
                image_links.append(data["href"])
                
        # Process client transaction IDs if they're in the JSON
        if "client_transaction_id" in data:
            if isinstance(data["client_transaction_id"], list):
                client_transaction_ids.extend(data["client_transaction_id"])
            elif isinstance(data["client_transaction_id"], str):
                client_transaction_ids.append(data["client_transaction_id"])
    
    # If transaction IDs aren't provided directly, we'll need to extract them from the URLs
    # Map image links to transaction IDs if needed
    if len(client_transaction_ids) != len(image_links):
        client_transaction_ids = []
        for link in image_links:
            # Extract the transaction ID from the URL path
            parsed_url = urlparse(link)
            path = parsed_url.path
            # The transaction ID is the last segment of the path
            path_segments = path.strip('/').split('/')
            if path_segments:
                client_transaction_ids.append(path_segments[-1])
            else:
                client_transaction_ids.append("unknown")
    
    print(f"Found {len(image_links)} image links with transaction IDs:")
    for i, (link, tx_id) in enumerate(zip(image_links, client_transaction_ids)):
        print(f"{i+1}. Link: {link}")
        print(f"   Transaction ID: {tx_id}")
    
    # Create a dummy printer for building the print job
    d = Dummy()
    
    # Download and print each image, then notify via callback
    for i, (link, tx_id) in enumerate(zip(image_links, client_transaction_ids)):
        try:
            print(f"Processing image {i+1}/{len(image_links)}: {link}")
            
            # Download the image
            img_response = requests.get(link)
            img_response.raise_for_status()
            
            # Create a temporary file for the image
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                tmp_file.write(img_response.content)
                tmp_path = tmp_file.name
            
            # Print the image
            d.image(tmp_path)
            d.cut()
            
            # Send to printer immediately after each image
            p._raw(d.output)
            
            # Create a new dummy for the next image
            d = Dummy()
            
            # Clean up the temporary file
            os.unlink(tmp_path)
            
            # Send callback notification with the client transaction ID
            # According to requirements, the client_transaction_id should be the last part of the URL path in the image link
            # Extract the receipt ID from the URL path which is what we need to send
            parsed_url = urlparse(link)
            path_segments = parsed_url.path.strip('/').split('/')
            receipt_id = path_segments[-1] if path_segments else "unknown"
            
            try:
                # Construct callback URL with query parameter
                callback_url = f"{CALLBACK_WEBHOOK_URL}?client_transaction_id={receipt_id}"
                print(f"Sending callback to: {callback_url}")
                
                # Use POST request to the callback URL
                callback_response = requests.post(callback_url)
                callback_response.raise_for_status()
                print(f"Callback sent for receipt ID: {receipt_id}")
                print(f"Callback response: {callback_response.status_code} {callback_response.text}")
            except requests.RequestException as callback_err:
                print(f"Error sending callback for receipt ID {receipt_id}: {callback_err}")
            
        except Exception as img_err:
            print(f"Error processing image {link}: {img_err}")
    
except requests.RequestException as e:
    print(f"Error fetching URL: {e}")
    
    # Create a dummy printer for error case
    d = Dummy()
    
    # Print only the default image in case of error
    d.image("TAAAXZ7TEME.png")
    d.cut()
    
    # Send code to printer
    p._raw(d.output)
