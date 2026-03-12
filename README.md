# nfc_reader

NFC Reader for Safebox with a reusable ACR122U/PCSC path.

## Use the project venv

The NFC dependencies are installed in the local virtual environment. Run the scripts with:

```bash
.venv/bin/python acr122u.py read --json
.venv/bin/python acr122u.py poll --json
.venv/bin/python acr122u.py uid
```

Running `python3` outside the venv will miss `pyscard` and `nfcpy`.

## ACR122U notes

The repo now treats the ACR122U as a PC/SC reader. If you see `PC/SC is unavailable`, start the system smart card service and reconnect the reader before retrying.

## Supported commands

- `acr122u.py read --json`: read card memory, extract `nembed`, and parse the payload.
- `acr122u.py poll --json`: poll continuously for card insert/remove events.
- `acr122u.py uid`: quick UID check.
- `acr122u.py write "nembed1..."`: write an `nembed` string as an NDEF text record.

The older `usb-*` and `read-card.py` entrypoints were removed to keep one canonical interface.
