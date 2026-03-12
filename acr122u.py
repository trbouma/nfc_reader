import argparse
import asyncio

from reader_core import NFCReaderError, connect, format_payload, read_card_payload, read_uid, write_ndef_text


def print_read_result(result, show_json: bool) -> None:
    print(f"Reader: {result.reader_name}")
    if result.uid_hex:
        print(f"UID: {result.uid_hex}")
    if result.nembed:
        print(f"\nExtracted Payload:\n{result.nembed}")
    else:
        print("No nembed payload found in card memory.")
    if show_json:
        print(f"\nParsed Payload:\n{format_payload(result.parsed_payload)}")


def read_once(show_json: bool) -> int:
    try:
        result = read_card_payload()
    except NFCReaderError as exc:
        print(exc)
        return 1

    print_read_result(result, show_json=show_json)
    return 0


async def poll_forever(show_json: bool, interval: float) -> int:
    last_uid = None
    last_error = None
    while True:
        try:
            result = read_card_payload()
            if result.uid_hex != last_uid:
                print_read_result(result, show_json=show_json)
                print()
                last_uid = result.uid_hex
            last_error = None
        except NFCReaderError as exc:
            message = str(exc)
            if message != last_error:
                print(message)
            if "No card present" in message:
                last_uid = None
            last_error = message
        await asyncio.sleep(interval)


def read_uid_once() -> int:
    try:
        reader, connection = connect()
        print(f"Reader: {reader}")
        uid_hex = read_uid(connection)
        if uid_hex:
            print(f"UID: {uid_hex}")
        else:
            print("Card UID is unavailable for this tag.")
        return 0
    except NFCReaderError as exc:
        print(exc)
        return 1


def write_once(nembed_string: str) -> int:
    if not nembed_string.startswith("nembed1"):
        print("Invalid string. It must start with 'nembed1'.")
        return 1

    try:
        reader, connection = connect()
        print(f"Reader: {reader}")
        bytes_written = write_ndef_text(connection, nembed_string)
        print(f"Wrote {bytes_written} bytes.")
        return 0
    except NFCReaderError as exc:
        print(exc)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Interact with an ACR122U over PC/SC.")
    subparsers = parser.add_subparsers(dest="command")

    read_parser = subparsers.add_parser("read", help="Read the current card once.")
    read_parser.add_argument("--json", action="store_true", help="Print parsed nembed JSON.")

    poll_parser = subparsers.add_parser("poll", help="Poll continuously for card insertions.")
    poll_parser.add_argument("--json", action="store_true", help="Print parsed nembed JSON.")
    poll_parser.add_argument("--interval", type=float, default=1.0, help="Polling interval in seconds.")

    subparsers.add_parser("uid", help="Read only the current card UID.")

    write_parser = subparsers.add_parser("write", help="Write an nembed string as an NDEF text record.")
    write_parser.add_argument("nembed", help="The nembed string to write.")

    args = parser.parse_args()

    if args.command in (None, "read"):
        return read_once(show_json=getattr(args, "json", False))
    if args.command == "poll":
        try:
            return asyncio.run(poll_forever(show_json=args.json, interval=args.interval))
        except KeyboardInterrupt:
            print("done")
            return 0
    if args.command == "uid":
        return read_uid_once()
    if args.command == "write":
        return write_once(args.nembed)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
