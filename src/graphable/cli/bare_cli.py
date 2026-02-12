import argparse
import sys
from pathlib import Path

from graphable.cli.commands.core import (
    check_command,
    checksum_command,
    convert_command,
    info_command,
    reduce_command,
    verify_command,
    write_checksum_command,
)


def run_bare():
    parser = argparse.ArgumentParser(
        prog="graphable", description="Graphable CLI (Bare-bones)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # info
    info_p = subparsers.add_parser("info", help="Get graph information")
    info_p.add_argument("file", type=Path, help="Input graph file")

    # check
    check_p = subparsers.add_parser("check", help="Validate graph (cycles/consistency)")
    check_p.add_argument("file", type=Path, help="Input graph file")

    # reduce
    reduce_p = subparsers.add_parser("reduce", help="Perform transitive reduction")
    reduce_p.add_argument("input", type=Path, help="Input graph file")
    reduce_p.add_argument("output", type=Path, help="Output graph file")
    reduce_p.add_argument(
        "--embed", action="store_true", help="Embed checksum in output"
    )

    # convert
    convert_p = subparsers.add_parser("convert", help="Convert between formats")
    convert_p.add_argument("input", type=Path, help="Input graph file")
    convert_p.add_argument("output", type=Path, help="Output graph file")
    convert_p.add_argument(
        "--embed", action="store_true", help="Embed checksum in output"
    )

    # checksum
    checksum_p = subparsers.add_parser("checksum", help="Calculate graph checksum")
    checksum_p.add_argument("file", type=Path, help="Graph file")

    # verify
    verify_p = subparsers.add_parser("verify", help="Verify graph checksum")
    verify_p.add_argument("file", type=Path, help="Graph file")
    verify_p.add_argument("--expected", help="Expected checksum (hex)")

    # write-checksum
    wc_p = subparsers.add_parser(
        "write-checksum", help="Write graph checksum to a file"
    )
    wc_p.add_argument("file", type=Path, help="Graph file")
    wc_p.add_argument("output", type=Path, help="Output checksum file")

    args = parser.parse_args()

    if args.command == "info":
        data = info_command(args.file)
        print(f"Nodes: {data['nodes']}")
        print(f"Edges: {data['edges']}")
        print(f"Sources: {', '.join(data['sources'])}")
        print(f"Sinks: {', '.join(data['sinks'])}")

    elif args.command == "check":
        data = check_command(args.file)
        if data["valid"]:
            print("Graph is valid.")
        else:
            print(f"Graph is invalid: {data['error']}")
            sys.exit(1)

    elif args.command == "reduce":
        reduce_command(args.input, args.output, embed_checksum=args.embed)
        print(f"Reduced graph saved to {args.output}")

    elif args.command == "convert":
        convert_command(args.input, args.output, embed_checksum=args.embed)
        print(f"Converted {args.input} to {args.output}")

    elif args.command == "checksum":
        print(checksum_command(args.file))

    elif args.command == "verify":
        data = verify_command(args.file, args.expected)
        if data["valid"] is True:
            print("Checksum verified.")
        elif data["valid"] is False:
            print(f"Checksum mismatch! Actual: {data['actual']}")
            sys.exit(1)
        else:
            print(f"No checksum found to verify. Current: {data['actual']}")

    elif args.command == "write-checksum":
        write_checksum_command(args.file, args.output)
        print(f"Checksum written to {args.output}")

    else:
        parser.print_help()


if __name__ == "__main__":
    run_bare()
