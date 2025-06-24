from smartcard.System import readers
from smartcard.util import toHexString

def main():
    # List all available readers
    available_readers = readers()
    if not available_readers:
        print("No smart card readers found.")
        return

    # Use the first reader
    reader = available_readers[0]
    print(f"Using reader: {reader}")

    # Connect to the card
    connection = reader.createConnection()
    connection.connect()

    print("Card connected.")

    # Example: Send APDU command to get UID (varies by card/reader)
    GET_UID_APDU = [0xFF, 0xCA, 0x00, 0x00, 0x00]

    response, sw1, sw2 = connection.transmit(GET_UID_APDU)

    if sw1 == 0x90 and sw2 == 0x00:
        print("Card UID:", toHexString(response))
    else:
        print(f"Failed to get UID. Status: {hex(sw1)} {hex(sw2)}")

if __name__ == "__main__":
    main()
