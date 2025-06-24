from smartcard.System import readers
from smartcard.util import toHexString

def create_ndef_text_record(text: str) -> bytes:
    lang = 'en'
    status_byte = len(lang)
    payload = bytes([status_byte]) + lang.encode('utf-8') + text.encode('utf-8')
    payload_len = len(payload)

    sr = payload_len < 256
    flags = 0xD1 if sr else 0xC1

    header = bytearray()
    header.append(flags)
    header.append(0x01)  # Type length = 1 ('T')

    if sr:
        header.append(payload_len)
    else:
        header += payload_len.to_bytes(4, 'big')

    header.append(0x54)  # Type = 'T'

    return bytes(header + payload)

def write_ndef_to_tag(reader, ndef_bytes: bytes):
    if len(ndef_bytes) <= 254:
        tlv = [0x03, len(ndef_bytes)] + list(ndef_bytes) + [0xFE]
    else:
        tlv = [0x03, 0xFF] + list(len(ndef_bytes).to_bytes(2, 'big')) + list(ndef_bytes) + [0xFE]

    # Pad to 4-byte alignment
    while len(tlv) % 4 != 0:
        tlv.append(0x00)

    print(f"\nTotal bytes to write: {len(tlv)}")
    print("Writing to tag...\n")

    for i in range(0, len(tlv), 4):
        page = 4 + i // 4
        block = tlv[i:i+4]

        if not all(isinstance(b, int) and 0 <= b <= 255 for b in block):
            raise Exception(f"Invalid byte in block: {block}")

        cmd = [0xFF, 0xD6, 0x00, page, 0x04] + block

        print(f"→ Writing Page {page:03}: {toHexString(block)}")
        response, sw1, sw2 = reader.transmit(cmd)

        if not (sw1 == 0x90 and sw2 == 0x00):
            raise Exception(f"Write failed at page {page}: SW1={sw1:X}, SW2={sw2:X}")

    print("\n✅ Write successful!")

def main():
    nembed_string = input("Enter nembed string (e.g., nembed1...): ").strip()

    if not nembed_string.startswith("nembed1"):
        print("❌ Invalid string. It must start with 'nembed1'")
        return

    r = readers()
    if not r:
        print("No NFC reader found.")
        return

    print(f"Using reader: {r[0]}")
    reader = r[0].createConnection()
    reader.connect()

    try:
        ndef = create_ndef_text_record(nembed_string)
        write_ndef_to_tag(reader, ndef)
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
