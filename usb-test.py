from smartcard.System import readers
import string
import re



def read_full_user_memory(reader, start_page=4, end_page=130):
    raw_bytes = bytearray()
    for page in range(start_page, end_page, 4):  # 4 pages = 16 bytes
        cmd = [0xFF, 0xB0, 0x00, page, 0x10]
        response, sw1, sw2 = reader.transmit(cmd)
        if sw1 == 0x90:
            raw_bytes.extend(response)
        else:
            raise Exception(f"Failed to read page {page}: SW1={sw1:X}, SW2={sw2:X}")
    return raw_bytes


def extract_nembed_string(raw_bytes):
    decoded = raw_bytes.decode('utf-8', errors='replace')

    # Find where 'nembed' starts
    marker = "nembed"
    start = decoded.find(marker)
    if start == -1:
        return "(marker 'nembed' not found)"

    candidate = decoded[start:]

    # Match Bech32-style string: nembed1 + valid charset + 6-char checksum
    match = re.match(r'(nembed1[023456789acdefghjklmnpqrstuvwxyz]{6,})(?![023456789acdefghjklmnpqrstuvwxyz])', candidate)
    if match:
        return match.group(1)

    # Fallback: keep only printable characters
    cleaned = ''.join(c for c in candidate if c in string.printable)
    return cleaned.strip()

def main():
    r = readers()
    if not r:
        print("No NFC reader found.")
        return

    reader = r[0].createConnection()
    reader.connect()

    try:
        raw_data = read_full_user_memory(reader, start_page=4, end_page=130)
        result = extract_nembed_string(raw_data)
        print(f"\nExtracted Payload:\n{result}")
        # parsed_nembed = parse_nembed_compressed(result)
        # print(raw_data)
    except Exception as e:
        # print(f"Error: {e}")
        print("insert card")

if __name__ == "__main__":
    main()
