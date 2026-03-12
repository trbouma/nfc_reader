from bech32 import bech32_decode, convertbits
import json, gzip, io

def parse_nembed_compressed(encoded_string):
    # Decode the Bech32 string
    hrp, data = bech32_decode(encoded_string)
    # print(f"hrp {hrp} data {data}")
    if hrp not in {"nembed"} or data is None:
        raise ValueError("Invalid Bech32 string or unsupported prefix")

    # Convert 5-bit data to 8-bit for processing
    decoded_data = bytes(convertbits(data, 5, 8, False))
    # this is gzipped data

    buffer = io.BytesIO(decoded_data)
    with gzip.GzipFile(fileobj=buffer, mode="rb") as gz:
        decompressed_data = gz.read()
    
    try:
        json_obj = json.loads(decompressed_data.decode())  
    except:
        json_obj = {}

    return json_obj