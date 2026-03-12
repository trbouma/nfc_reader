# nfc_reader

NFC Reader for Safebox with a single reusable ACR122U/PCSC CLI.

## Setup

Create the virtual environment and install dependencies with Poetry:

```bash
poetry install
```

If you want Poetry to place the virtual environment inside the repo as `.venv`, run:

```bash
poetry config virtualenvs.in-project true
poetry install
```

Then use the project virtual environment:

```bash
.venv/bin/python acr122u.py --help
```

You can also run commands through Poetry directly:

```bash
poetry run python acr122u.py --help
```

Running `python3` outside the venv will miss the NFC dependencies.

## Reader

This project is built around the ACS ACR122U USB NFC reader. It is a 13.56 MHz contactless smart card reader that presents itself as a CCID/PC/SC device, which is why this repo talks to it through `pyscard` instead of a vendor-specific USB protocol. In practice, the code expects an ACR122U-compatible PC/SC reader and reads NFC tag memory using APDU commands exposed by the reader firmware.

The repo treats the ACR122U as a PC/SC reader. If you see `PC/SC is unavailable`, start the smart card service and reconnect the reader before retrying.

## Key tests

### 1. Reader and card connectivity

Use this first to confirm the ACR122U is visible and a card can be selected:

```bash
.venv/bin/python acr122u.py uid
```

Expected result:
- Prints the reader name and the card UID.

### 2. Read the card payload

Use this to confirm the card memory contains a valid Safebox `nembed` payload:

```bash
.venv/bin/python acr122u.py read --json
```

Expected result:
- Prints the reader, UID, extracted `nembed` string, and parsed JSON payload.

### 3. Fetch the live balance

Use this to verify the documented Safebox server flow for `/.well-known/card-balance`:

```bash
.venv/bin/python acr122u.py balance
```

Expected result:
- Prints the live integer balance returned by the Safebox server.

### 4. Poll for card insert/remove events

Use this when testing repeated taps or swapping cards:

```bash
.venv/bin/python acr122u.py poll --json
```

Expected result:
- Prints payload details once per newly inserted card.
- Resets cleanly when the card is removed.

### 5. Poll and return only balances

Use this for balance-check kiosk behavior:

```bash
.venv/bin/python acr122u.py poll-balance
```

Expected result:
- Waits for a card.
- Prints the live balance once per newly inserted card.

### 6. Write a test card and read it back

Use this to write a known `nembed` string as an NDEF text record:

```bash
.venv/bin/python acr122u.py write "nembed1..."
```

Then verify it with:

```bash
.venv/bin/python acr122u.py read --json
```

## Supported commands

- `acr122u.py read --json`
- `acr122u.py poll --json`
- `acr122u.py uid`
- `acr122u.py balance`
- `acr122u.py poll-balance`
- `acr122u.py write "nembed1..."`
