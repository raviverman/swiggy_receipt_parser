#!/usr/bin/env python3

import pdfplumber
import yaml
import re
import json
import pdb
import argparse
from typing import Any, Dict, List


class SchemaError(Exception):
    pass

class ValidationError(Exception):
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("\n".join(errors))

def load_schema(path: str) -> Dict:
    with open(path) as f:
        return yaml.safe_load(f)

def extract_text(pdf_path: str) -> str:
    text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text.append(t)
    return "\n".join(text)

def cast(value: str, to_type: str):
    try:
        if to_type == "int":
            return int(float(value))
        if to_type == "float":
            return float(value)
        return value.strip()
    except Exception:
        pass # ignore type cast failure, leave it as string
    return value

def extract_fields(section: Dict, text: str, errors: List[str]) -> Dict:
    '''
    Parses schema fields and from the input text.
    '''
    result = {}
    for field, rule in section.items():
        match = re.search(rule["regex"], text)
        if not match:
            if rule.get("required"):
                errors.append(f"[MISSING] {field}")
            continue

        value = match.group(1)
        try:
            value = cast(value, rule.get("type", "str"))
        except Exception as e:
            errors.append(f"[TYPE] {field}: {e}")
            continue
        result[field] = value
    return result

def flatten_fields(schema: Dict, parent_key : str ="") -> Dict:
    '''
    Makes nested keys flattened by concatenating them using a colon
    '''
    result = {}
    for key, value in schema.items():
        if 'regex' in value.keys():
            # base field
            newkey = f"{parent_key}:{key}" if parent_key else key
            result.update({newkey : value})
        else:
            output = flatten_fields(value, key)
            result.update(output)
    return result

def nest_fields(schema: Dict) -> Dict:
    '''
    Makes flattened keys nested by splitting them using a colon
    '''
    result = {}
    for key, value in schema.items():
        # if the key has ':' in the keyname, it needs nesting
        if ':' in key:
            prefixes = key.split(":")
            obj = result
            for prefix in prefixes:
                if prefix == prefixes[-1]:
                    obj.setdefault(prefix, value)
                    break
                obj.setdefault(prefix, {})   
                obj = obj[prefix]
        else:
            result.update( { key: value} )
    return result

def extract_invoice_fields(schema: Dict, row : List[str], errors: List[str]) ->Dict:
    '''
    Invoice fields are a bit complicated. There are two columns in the PDF.
    All invoice fields are present in one cell separated by new lines. These
    lines are split on \\n and also called rows below.
    e.g. 
    Field1: Single_Line_Value            Field2: MutliLine Value
                                                 that drops to new line
    Any such row can contain partial info of any column and any row may contain
    next line of the previous row from any column.
    Pray that no multiline columns are present side by side in a column or
    this parser will return wrong results.
    '''
    result = {}
    # Only the first cell has all the invoice details
    text = join_table_cells(row)
    # split by new lines
    rows  = text.split("\n")
    # build flat field to regex mapping, will be nested later on
    fields = flatten_fields(schema)
    flat_parsed = {}
    order_of_key = [] # needed to append multiline rows to previously parsed rows
    for r in rows:
        this_iteration = {}
        for field, value in fields.items():
            if field in flat_parsed: # already found
                continue
            match = re.search( value['regex'], r)
            if match:
                cast_value = cast( match.group(1), value.get('type', 'str'))
                this_iteration.update({ field : cast_value })

        if this_iteration:
            order_of_key += list(this_iteration.keys())
            flat_parsed.update(this_iteration)
        else:
            # not a match. the value is likely from previous field
            for prev_field in order_of_key[-2:]:
                if fields[prev_field].get('multiline', False):
                    flat_parsed[prev_field] += f"\n{r}"

   # first column values can have fields from other columns, find and replace them
    for parsed_field, parsed_value in flat_parsed.items():
        for sch_field, sch_value in fields.items():
            match = re.search( sch_value['regex'], parsed_value)
            if match:
                flat_parsed[ parsed_field ] = parsed_value.replace(match.group(0), "")
                value = flat_parsed[ parsed_field ]
                cast_value = cast( value, fields[parsed_field].get('type', 'str'))
                flat_parsed[ parsed_field ] = cast_value

    # nest fields
    result = nest_fields(flat_parsed)
    return result;

def join_table_cells(row:List[str], separator : str = " ", replace_nl:bool=False) -> str:
    '''
    A PDF table can look like [ "text", None, None, "text" ]
    This function ignore None and joins the rest of the fields. If required,
    also removes the new line character.
    '''
    string = f"{separator}".join(filter(lambda x: x, row))
    if replace_nl:
        string = string.replace("\n", " " )
    return string

def extract_invoice(pdf_path: str, table_schema: Dict, errors: List[str]) -> List[Dict]:
    '''
    The main invoice parser. This function containes stages to parse different
    invoice sections. It determines what kind of invoice it is and then
    uses appropriate schema.
    Stages:
    1. Invoice Headers (Seller, Buyer, InvoiceId etc. )
    2. Items in the invoice ( Items bought )
    3. Invoice trailer ( Total, Taxes )
    '''
    invoice_headers = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                tables = tables[0]
            for i in range(0, len(tables)):
                table = tables[i]
                if not table or not table[0]:
                    # skip empty table rows
                    continue
                header = join_table_cells( table, replace_nl=True)
                if header == table_schema[ 'invoice' ][ 'header' ]:
                    i +=1
                    table = tables[i]
                # Section1: Headers (parse the invoice header sections)
                errors = []
                schema_name = 'third_party' if i == 1 else 'swiggy'
                invoice_fields = extract_invoice_fields(
                    table_schema['invoice'][schema_name], table, errors )
                invoice_headers.update({
                   invoice_fields[ 'invoice_no' ] : invoice_fields
                })
                if errors:
                    raise ValidationError( errors )
                # Section2: Item Tables (parse the table items)
                item_schema = table_schema[ "items" ][ schema_name ]
                # Iterate till you find the start of the items table
                for next_iter in range(i, len(tables)):
                    table = tables[next_iter]
                    header = join_table_cells( table, replace_nl=True)
                    if item_schema["header_contains"] not in header:
                        continue
                    i = next_iter
                    break

                remaining_table, items = parse_table_items( item_schema, tables[i+1:] )
                invoice_headers[invoice_fields[ 'invoice_no' ]]['items'] = items

                # Section3: Trailer
                trailer = parse_trailer(table_schema[ 'trailer'][ schema_name ], remaining_table)
                invoice_headers[invoice_fields[ 'invoice_no' ]]['trailer'] = trailer
                # process no more tables in this page
                break

    return invoice_headers

def parse_trailer(schema:Dict, table:List[str])->List:
    '''
    This function converts table rows into strings and based on schema
    i.e. field and regex, returns a dictionary of key, values
    '''
    errors = []
    trailer = {}
    for row in table:
        row_as_str = join_table_cells( row, replace_nl=True )
        trailer.update(extract_fields(schema, row_as_str, errors))
    if errors:
        raise ValidationError( errors )
    return trailer

def parse_table_items(schema:Dict, table:List[str]) -> List:
    '''
    This function converts actual table with rows and cols to a list of 
    objects representing a col. The schema defines the key names of the object.
    '''
    items = []
    for row_idx, row in enumerate(table, start=1):
        if not row or not row[0] or not row[0].strip(".").isdigit():
            return (table[row_idx-1:], items)
        item = {}
        for col, spec in schema["columns"].items():
            idx = spec["index"]
            try:
                raw = row[idx]
                item[col] = cast(raw, spec["type"])
            except Exception as e:
                errors.append(
                    f"[ITEM ROW {row_idx}] column '{col}': {e}"
                )

        items.append(item)
    return ([], items)

def parse_pdf(pdf_path: str, schema: Dict, validate_only=False) -> Dict:
    errors = []
    output = {}

    output["invoice"] = extract_invoice(
        pdf_path, schema, errors
    )
    if errors:
        raise ValidationError(errors)
    return output if not validate_only else {}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", help="PDF file path")
    parser.add_argument("--schema", required=True)
    parser.add_argument("--validate", action='store_true', help="Only validate")
    args = parser.parse_args()

    schema = load_schema(args.schema)

    try:
        result = parse_pdf(args.pdf, schema, validate_only=args.validate)
        if args.validate:
            print("✓ PDF conforms to schema")
        else:
            print(json.dumps(result, indent=2))
    except ValidationError as e:
        print("✕ Schema validation failed:\n")
        for err in e.errors:
            print(" -", err)
        exit(1)


if __name__ == "__main__":
    main()
