#!/usr/bin/env python3

import mailbox
import os
import pdb
import argparse
from email.utils import parsedate_to_datetime

def extract_pdfs(mbox_path):
    # Load the mbox file
    if not os.path.exists(mbox_path):
        print(f"Error: {mbox_path} not found.")
        return

    mbox = mailbox.mbox(mbox_path)
    print(f"Mbox file loaded: {mbox_path}")
    print(f"Number of messages found by mailbox.mbox: {len(mbox)}")
    
    extracted_count = 0
    
    for i, message in enumerate(mbox):
        print(f"Processing message {i+1}")
        # Extract the date from the email header
        date_str = message.get('Date')
        if not date_str:
            print(f"  Skipping message {i+1}: No Date header found.")
            continue
            
        try:
            # Parse the date string into a datetime object
            dt = parsedate_to_datetime(date_str)
            # Format: swiggy_dd_mm_yy_hh_mm_ss.pdf
            filename_base = dt.strftime("%d_%m_%y_%H_%M_%S")
        except Exception as e:
            print(f"  Skipping message {i+1}: ",
                  f"Error parsing date '{date_str}': {e}")
            continue

        # Iterate through the message parts to find attachments
        for part_index, part in enumerate(message.walk()):
            # Skip containers (multipart parts usually have other parts)
            if part.is_multipart():
                continue
                
            content_type = part.get_content_type()
            filename_param = part.get_filename()
            
            is_pdf = False
            is_instamart = False 
            # Check if content type is application/pdf or
            # application/octet-stream with a PDF filename
            if content_type == "application/pdf":
                is_pdf = True
            if content_type == "application/octet-stream" and \
                filename_param.endswith("pdf"):
                # usually a instamart receipt because it's merged pdf
                # with two pages
                is_pdf = True
                is_instamart = True
            # Check if the part is a PDF
            instamart = "_instamart" if is_instamart else ""

            if is_pdf:
                print(f"  Found potential PDF attachment in message {i+1}, ",
                      f"part {part_index}: Content-Type={content_type}, ",
                      f"Filename={filename_param}")
                # get_payload(decode=True) handles the base64 decoding
                # automatically
                payload = part.get_payload(decode=True)
                if payload:
                    # Handle potential filename collisions for multiple
                    # attachments in one mail
                    filename = f"swiggy{instamart}_{filename_base}.pdf"
                    
                    # Ensure we don't overwrite if multiple PDFs arrive
                    # at the exact same second
                    counter = 1
                    while os.path.exists(filename):
                        filename = f"{filename}_{counter}.pdf"
                        counter += 1
                        
                    with open(filename, 'wb') as f:
                        f.write(payload)
                    
                    print(f"Saved: {filename}")
                    extracted_count += 1

    print(f"\nFinished extraction. Total PDFs saved: {extracted_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Extract PDF attachments from an mbox file.')
    parser.add_argument('mbox_file', help='Path to the .mbox file')
    args = parser.parse_args()
    
    extract_pdfs(args.mbox_file)
