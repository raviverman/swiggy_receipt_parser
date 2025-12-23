# Swiggy PDF Receipt Parser

This repo contains two scripts.
1. To extract swiggy pdfs receipts from mails stored in an mbox file.
2. To parse these pdfs and generate json.

## Running the script locally

1. Make sure you've all the python dependencies installed.

    `pip3 install -r requirements.txt`

2. Extract pdfs from the mbox file.

    `./extract_swiggy_pdfs.py mails.mbox`

3. Parse pdf to json.

    `./parse_receipts.py --schema instamart_schema.yaml <receipt>.pdf`

4. Only validate if pdf can be parsed to json.

    `./parse_receipts.py --schema instamart_schema.yaml <receipt>.pdf --validate`

## Running the docker image.

```sh
docker build -t swiggy:latest .
mkdir ./data
# If you have pdf files
cp *.pdf ./data
docker run -v ./data:/app/data swiggy:latest
# If you have mbox file
cp *.mbox ./data
docker run -e MBOX_FILE=/app/datai/mails.mbox -v ./data:/app/data swiggy:latest
```

## How to get an mbox file
An mbox file is a collection of mails stored in plain text format. The
attachments are encoded into base64 and then written to the file.

### Getting an mbox file for all swiggy mails
1. Add a filter on Google Mail to filter all swiggy mails.
    - Has instamart in string.
    - Has attachment.
    - Assign a new label to these mails (Don't forget to apply filter to existing matches).

2. Go to [Google Takeout](https://takeout.google.com)
    - Deselect all items.
    - Select mails and only the new label.
    - Export.

3. Refresh the page and download the archive.

