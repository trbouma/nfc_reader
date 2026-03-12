from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import string
from typing import Any

from monstr.encrypt import Keys
import requests
import secp256k1
from smartcard.Exceptions import CardConnectionException, NoCardException, SmartcardException
from smartcard.System import readers
from smartcard.pcsc.PCSCExceptions import EstablishContextException
from smartcard.util import toHexString

from utils import parse_nembed_compressed


GET_UID_APDU = [0xFF, 0xCA, 0x00, 0x00, 0x00]
READ_CHUNK_SIZE = 0x10
WRITE_BLOCK_SIZE = 0x04


class NFCReaderError(RuntimeError):
    pass


@dataclass
class CardReadResult:
    reader_name: str
    uid_hex: str | None
    raw_data: bytes
    nembed: str | None
    parsed_payload: dict[str, Any] | None


def extract_default_amount(parsed_payload: dict[str, Any] | None) -> int:
    if parsed_payload is None:
        raise NFCReaderError("No parsed payload is available for this card.")

    amount = parsed_payload.get("a")
    if amount is None:
        raise NFCReaderError("The card payload does not contain a default amount field ('a').")
    if not isinstance(amount, int):
        raise NFCReaderError(f"The default amount must be an integer, got {type(amount).__name__}.")
    return amount


def list_readers() -> list[Any]:
    try:
        return list(readers())
    except EstablishContextException as exc:
        raise NFCReaderError(
            "PC/SC is unavailable. Start the smart card service and reconnect the ACR122U."
        ) from exc
    except Exception as exc:
        raise NFCReaderError(f"Unable to enumerate smart card readers: {exc}") from exc


def get_reader(reader_index: int = 0) -> Any:
    available = list_readers()
    if not available:
        raise NFCReaderError("No smart card readers found. Check the ACR122U USB connection.")
    if reader_index < 0 or reader_index >= len(available):
        raise NFCReaderError(
            f"Reader index {reader_index} is out of range. {len(available)} reader(s) detected."
        )
    return available[reader_index]


def connect(reader_index: int = 0):
    reader = get_reader(reader_index)
    connection = reader.createConnection()
    try:
        connection.connect()
    except NoCardException as exc:
        raise NFCReaderError("No card present on the ACR122U.") from exc
    except CardConnectionException as exc:
        raise NFCReaderError(f"Unable to connect to the card on reader '{reader}'.") from exc
    except SmartcardException as exc:
        raise NFCReaderError(f"Smart card communication failed on reader '{reader}': {exc}") from exc
    return reader, connection


def read_uid(connection) -> str | None:
    response, sw1, sw2 = connection.transmit(GET_UID_APDU)
    if (sw1, sw2) == (0x90, 0x00):
        return toHexString(response)
    return None


def read_full_user_memory(connection, start_page: int = 4, end_page: int = 130) -> bytes:
    raw_bytes = bytearray()
    for page in range(start_page, end_page, 4):
        cmd = [0xFF, 0xB0, 0x00, page, READ_CHUNK_SIZE]
        try:
            response, sw1, sw2 = connection.transmit(cmd)
        except NoCardException as exc:
            raise NFCReaderError("Card was removed during the read.") from exc
        except SmartcardException as exc:
            error_message = str(exc)
            if "Card returned no valid response" in error_message:
                raise NFCReaderError("Card was removed during the read.") from exc
            raise NFCReaderError(f"Read failed at page {page}: {exc}") from exc
        if (sw1, sw2) != (0x90, 0x00):
            raise NFCReaderError(f"Read failed at page {page}: SW1={sw1:02X}, SW2={sw2:02X}")
        raw_bytes.extend(response)
    return bytes(raw_bytes)


def extract_nembed_string(raw_bytes: bytes) -> str | None:
    decoded = raw_bytes.decode("utf-8", errors="replace")
    start = decoded.find("nembed")
    if start == -1:
        return None

    candidate = decoded[start:]
    match = re.match(
        r"(nembed1[023456789acdefghjklmnpqrstuvwxyz]{6,})(?![023456789acdefghjklmnpqrstuvwxyz])",
        candidate,
    )
    if match:
        return match.group(1)

    cleaned = "".join(ch for ch in candidate if ch in string.printable).strip()
    return cleaned or None


def read_card_payload(reader_index: int = 0, start_page: int = 4, end_page: int = 130) -> CardReadResult:
    reader, connection = connect(reader_index)
    uid_hex = read_uid(connection)
    raw_data = read_full_user_memory(connection, start_page=start_page, end_page=end_page)
    nembed = extract_nembed_string(raw_data)
    parsed_payload = None
    if nembed:
        parsed_payload = parse_nembed_payload(nembed)
    return CardReadResult(
        reader_name=str(reader),
        uid_hex=uid_hex,
        raw_data=raw_data,
        nembed=nembed,
        parsed_payload=parsed_payload,
    )


def read_card_balance(reader_index: int = 0, start_page: int = 4, end_page: int = 130) -> int:
    result = read_card_payload(reader_index=reader_index, start_page=start_page, end_page=end_page)
    return fetch_card_balance(result.parsed_payload)


def parse_nembed_payload(nembed_string: str) -> dict[str, Any]:
    parsed_payload = parse_nembed_compressed(nembed_string)
    if not parsed_payload:
        raise NFCReaderError("The nembed payload decoded, but it did not contain valid JSON.")
    return parsed_payload


def format_payload(parsed_payload: dict[str, Any] | None) -> str:
    if parsed_payload is None:
        return "(no parsed payload)"
    return json.dumps(parsed_payload, indent=2, sort_keys=True)


def build_card_balance_request(parsed_payload: dict[str, Any] | None) -> tuple[str, dict[str, str]]:
    if parsed_payload is None:
        raise NFCReaderError("No parsed payload is available for this card.")

    host = parsed_payload.get("h")
    token = parsed_payload.get("k")
    if not isinstance(host, str) or not host:
        raise NFCReaderError("The card payload does not contain a valid host ('h').")
    if not isinstance(token, str) or not token:
        raise NFCReaderError("The card payload does not contain a valid token ('k').")

    keys = Keys()
    private_key = secp256k1.PrivateKey(bytes.fromhex(keys.private_key_hex()), raw=True)
    token_digest = hashlib.sha256(token.encode("utf-8")).digest()
    signature = private_key.schnorr_sign(token_digest, None, raw=True).hex()

    url = f"https://{host}/.well-known/card-balance"
    body = {
        "token": token,
        "pubkey": keys.public_key_hex(),
        "sig": signature,
    }
    return url, body


def extract_remote_balance(response_json: Any) -> int:
    if not isinstance(response_json, dict):
        raise NFCReaderError("Card balance response was not a JSON object.")

    for key in ("balance", "balance_sats", "amount", "card_balance"):
        value = response_json.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)

    raise NFCReaderError(f"Card balance response did not include a recognized integer balance field: {response_json}")


def fetch_card_balance(parsed_payload: dict[str, Any] | None, timeout: float = 10.0) -> int:
    url, body = build_card_balance_request(parsed_payload)
    try:
        response = requests.post(url, json=body, timeout=timeout)
    except requests.RequestException as exc:
        raise NFCReaderError(f"Card balance request failed: {exc}") from exc

    try:
        response_json = response.json()
    except ValueError as exc:
        raise NFCReaderError(f"Card balance response was not valid JSON: {response.text}") from exc

    if response.status_code != 200:
        raise NFCReaderError(
            f"Card balance request failed with HTTP {response.status_code}: {response_json}"
        )

    return extract_remote_balance(response_json)


def create_ndef_text_record(text: str) -> bytes:
    lang = "en"
    status_byte = len(lang)
    payload = bytes([status_byte]) + lang.encode("utf-8") + text.encode("utf-8")
    payload_len = len(payload)

    short_record = payload_len < 256
    flags = 0xD1 if short_record else 0xC1

    header = bytearray([flags, 0x01])
    if short_record:
        header.append(payload_len)
    else:
        header.extend(payload_len.to_bytes(4, "big"))
    header.append(0x54)

    return bytes(header + payload)


def build_ndef_tlv(ndef_bytes: bytes) -> list[int]:
    if len(ndef_bytes) <= 254:
        tlv = [0x03, len(ndef_bytes)] + list(ndef_bytes) + [0xFE]
    else:
        tlv = [0x03, 0xFF] + list(len(ndef_bytes).to_bytes(2, "big")) + list(ndef_bytes) + [0xFE]

    while len(tlv) % WRITE_BLOCK_SIZE != 0:
        tlv.append(0x00)
    return tlv


def write_ndef_text(connection, text: str, start_page: int = 4) -> int:
    ndef_bytes = create_ndef_text_record(text)
    tlv = build_ndef_tlv(ndef_bytes)

    for offset in range(0, len(tlv), WRITE_BLOCK_SIZE):
        page = start_page + offset // WRITE_BLOCK_SIZE
        block = tlv[offset : offset + WRITE_BLOCK_SIZE]
        cmd = [0xFF, 0xD6, 0x00, page, WRITE_BLOCK_SIZE] + block
        try:
            _, sw1, sw2 = connection.transmit(cmd)
        except SmartcardException as exc:
            raise NFCReaderError(f"Write failed at page {page}: {exc}") from exc
        if (sw1, sw2) != (0x90, 0x00):
            raise NFCReaderError(f"Write failed at page {page}: SW1={sw1:02X}, SW2={sw2:02X}")
    return len(tlv)
