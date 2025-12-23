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

## Examples

1. Parsing a food order into json.

```sh
shell> src/parse_receipts.py --schema src/food_order.yaml swiggy_01_09_25_16_42_31.pdf
{
  "invoice": {
    "0267542090100061": {
      "buyer": {
        "invoice_to": "Sherlock Holmes",
        "gstin": "Unregistered",
        "address": "221B Baker St. London"
      },
      "seller": {
        "name": "Mumtaz Restaurant",
        "gstin": "29ABICS2114G1ZI",
        "fssai": "11221333001398",
        "address": "4-10 Park Rd, London",
        "state": "UK"
      },
      "doc_type": "INV",
      "place_of_supply": "UK",
      "invoice_no": "0267542090100061",
      "service_desc": "Restaurant Service",
      "invoice_date": "01-09-2025",
      "category": "B2C",
      "reverse_charge_applicable": "No",
      "items": [
        {
          "sr_no": 1,
          "description": "Chole Bhature",
          "unit_of_measure": "OTH",
          "quantity": 1,
          "unit_price": 222.0,
          "amount": 222.0,
          "discount": 64.0,
          "net_assessable_value": 158.0,
          "total_amount": 158.0
        },
        {
          "sr_no": 2,
          "description": "Order Packing Charges",
          "unit_of_measure": "OTH",
          "quantity": 1,
          "unit_price": 13.29,
          "amount": 13.29,
          "discount": 0.0,
          "net_assessable_value": 13.29,
          "total_amount": 13.29
        }
      ],
      "trailer": {
        "cgst_percent": 2.5,
        "cgst_amount": 4.28,
        "sgst_percent": 2.5,
        "sgst_amount": 4.28,
        "igst_percent": 0.0,
        "igst_amount": 0.0,
        "total_taxes": 8.56,
        "invoice_value": 179.85
      }
    }
  }
}
```

2. Parsing an instamart order into json.
```sh
shell> src/parse_receipts.py --schema src/instamart_schema.yaml swiggy_instamart_25_06_25_15_59_57.pdf
{
  "invoice": {
    "250625IMAPR01261": {
      "seller": {
        "name": "Tesco Express",
        "gstin": "29ABDCS3851Q1ZL",
        "fssai": "11224333000035",
        "address": "11-15 Melcombe St, London",
        "city": "London"
      },
      "buyer": {
        "name": "Sherlock Holmes",
        "gstin": "Unregistered",
        "address": "221B Baker St. London"
      },
      "order_id": "209836216565241",
      "invoice_no": "250625IMAPR01261",
      "invoice_date": "25-06-2025",
      "items": [
        {
          "sr_no": 1,
          "description": "French Beans (Bili\nHurulikaayi)",
          "quantity": 1,
          "uom": "NOS",
          "hsn": "07031010",
          "taxable_value": 35.0,
          "discount": 7.0,
          "net_taxable_value": 28.0,
          "cgst_rate": 0.0,
          "cgst_amount": 0.0,
          "sgst_rate": 0.0,
          "sgst_amount": 0.0,
          "total_amount": 28.0
        },
        {
          "sr_no": 2,
          "description": "Kurkure Namkeen\nChilli Chatka",
          "quantity": 2,
          "uom": "NOS",
          "hsn": "21069099",
          "taxable_value": 35.71,
          "discount": 0.36,
          "net_taxable_value": 35.36,
          "cgst_rate": 6.0,
          "cgst_amount": 2.12,
          "sgst_rate": 6.0,
          "sgst_amount": 2.12,
          "total_amount": 39.6
        },
        {
          "sr_no": 3,
          "description": "Kurkure Namkeen\nMasala Munch",
          "quantity": 1,
          "uom": "NOS",
          "hsn": "21069099",
          "taxable_value": 17.86,
          "discount": 0.0,
          "net_taxable_value": 17.86,
          "cgst_rate": 6.0,
          "cgst_amount": 1.07,
          "sgst_rate": 6.0,
          "sgst_amount": 1.07,
          "total_amount": 20.0
        },
        {
          "sr_no": 4,
          "description": "Fortune Kachi\nGhani Mustard Oil",
          "quantity": 1,
          "uom": "NOS",
          "hsn": "15149120",
          "taxable_value": 204.76,
          "discount": 33.33,
          "net_taxable_value": 171.43,
          "cgst_rate": 2.5,
          "cgst_amount": 4.29,
          "sgst_rate": 2.5,
          "sgst_amount": 4.29,
          "total_amount": 180.0
        }
      ],
      "trailer": {
        "invoice_value": 267.6
      }
    },
    "250625SWIM846312": {
      "seller": {
        "name": "Swiggy Limited (formerly known as Swiggy \nPrivate Limited and Bundl Technologies Private\nLimited)",
        "pan": "ACB11AC9393",
        "gstin": "29AAFCB2707D1ZR",
        "address": "11-15 Melcombe St, London",
        "pin_code": 443330035883,
        "state_code": 29
      },
      "buyer": {
        "invoice_to": "Customer",
        "name": "Sherlock Holmes",
        "category": "B2C",
        "txn_type": "REG"
      },
      "doc_type": "INV",
      "inv_type": "RG",
      "invoice_no": "250625SWIM846312",
      "invoice_date": "25-06-2025",
      "reverse_charge_applicable": "No",
      "items": [
        {
          "sr_no": 1,
          "description": "Handling Fees for Order 209836216565241",
          "hsn": "999799",
          "unit_of_measure": "OTH",
          "quantity": 1,
          "unit_price": 9.797,
          "amount": 9.797,
          "discount": 0.0,
          "net_assessable_value": 9.8,
          "total_amount": 9.8
        }
      ],
      "trailer": {
        "cgst_percent": 9.0,
        "sgst_percent": 9.0,
        "sgst_amount": 0.88,
        "state_cess_percent": 0.0,
        "state_cess_amount": 0.0,
        "total_taxes": 1.76,
        "invoice_value": 11.56
      }
    }
  }
}
```
