import argparse
import sys
from pathlib import Path

from graphable.cli.commands.core import (
    check_command,
    checksum_command,
    convert_command,
    diff_command,
    diff_visual_command,
    info_command,
    reduce_command,
    render_command,
    verify_command,
    write_checksum_command,
)
from graphable.enums import Engine


def run_bare():
    parser = argparse.ArgumentParser(
        prog="graphable", description="Graphable CLI (Bare-bones)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # info
    info_p = subparsers.add_parser("info", help="Get graph information")
    info_p.add_argument("file", type=Path, help="Input graph file")
    info_p.add_argument("-t", "--tag", help="Filter by tag")

    # check
    check_p = subparsers.add_parser("check", help="Validate graph (cycles/consistency)")
    check_p.add_argument("file", type=Path, help="Input graph file")
    check_p.add_argument("-t", "--tag", help="Filter by tag")

    # reduce
    reduce_p = subparsers.add_parser("reduce", help="Perform transitive reduction")
    reduce_p.add_argument("input", type=Path, help="Input graph file")
    reduce_p.add_argument("output", type=Path, help="Output graph file")
    reduce_p.add_argument(
        "--embed", action="store_true", help="Embed checksum in output"
    )
    reduce_p.add_argument("-t", "--tag", help="Filter by tag")

    # convert
    convert_p = subparsers.add_parser("convert", help="Convert between formats")
    convert_p.add_argument("input", type=Path, help="Input graph file")
    convert_p.add_argument("output", type=Path, help="Output graph file")
    convert_p.add_argument(
        "--embed", action="store_true", help="Embed checksum in output"
    )
    convert_p.add_argument("-t", "--tag", help="Filter by tag")

    # render
    render_p = subparsers.add_parser("render", help="Render graph as image")
    render_p.add_argument("input", type=Path, help="Input graph file")
    render_p.add_argument("output", type=Path, help="Output image file (.png, .svg)")
    render_p.add_argument(
        "-e", "--engine", choices=[e.value.lower() for e in Engine], help="Rendering engine"
    )
    render_p.add_argument("-t", "--tag", help="Filter by tag")

    # checksum
    checksum_p = subparsers.add_parser("checksum", help="Calculate graph checksum")
    checksum_p.add_argument("file", type=Path, help="Graph file")
    checksum_p.add_argument("-t", "--tag", help="Filter by tag")

    # verify
    verify_p = subparsers.add_parser("verify", help="Verify graph checksum")
    verify_p.add_argument("file", type=Path, help="Graph file")
    verify_p.add_argument("--expected", help="Expected checksum (hex)")
    verify_p.add_argument("-t", "--tag", help="Filter by tag")

    # write-checksum
    wc_p = subparsers.add_parser(
        "write-checksum", help="Write graph checksum to a file"
    )
    wc_p.add_argument("file", type=Path, help="Graph file")
    wc_p.add_argument("output", type=Path, help="Output checksum file")
    wc_p.add_argument("-t", "--tag", help="Filter by tag")

    # diff
    diff_p = subparsers.add_parser("diff", help="Compare two graphs")
    diff_p.add_argument("file1", type=Path, help="First graph file")
    diff_p.add_argument("file2", type=Path, help="Second graph file")
    diff_p.add_argument("-o", "--output", type=Path, help="Output file for visual diff")
    diff_p.add_argument("-t", "--tag", help="Filter by tag")

    # serve
    serve_p = subparsers.add_parser("serve", help="Serve interactive visualization")
    serve_p.add_argument("file", type=Path, help="Graph file to serve")
    serve_p.add_argument("--port", type=int, default=8000, help="Port to serve on")
    serve_p.add_argument("-t", "--tag", help="Filter by tag")

    args = parser.parse_args()

    if args.command == "info":
        data = info_command(args.file, tag=args.tag)
        print(f"Nodes: {data['nodes']}")
        print(f"Edges: {data['edges']}")
        print(f"Sources: {', '.join(data['sources'])}")
        print(f"Sinks: {', '.join(data['sinks'])}")
        if data.get("project_duration") is not None:
            print(f"Project Duration: {data['project_duration']}")
            print(f"Critical Path Length: {data['critical_path_length']}")

    elif args.command == "check":
        data = check_command(args.file, tag=args.tag)
        if data["valid"]:
            print("Graph is valid.")
        else:
            print(f"Graph is invalid: {data['error']}")
            sys.exit(1)

    elif args.command == "reduce":
        reduce_command(args.input, args.output, embed_checksum=args.embed, tag=args.tag)
        print(f"Reduced graph saved to {args.output}")

    elif args.command == "convert":
        convert_command(
            args.input, args.output, embed_checksum=args.embed, tag=args.tag
        )
        print(f"Converted {args.input} to {args.output}")

    elif args.command == "render":
        render_command(args.input, args.output, engine=args.engine, tag=args.tag)
        print(f"Rendered {args.input} to {args.output}")

    elif args.command == "checksum":
        print(checksum_command(args.file, tag=args.tag))

    elif args.command == "verify":
        data = verify_command(args.file, args.expected, tag=args.tag)
        if data["valid"] is True:
            print("Checksum verified.")
        elif data["valid"] is False:
            print(f"Checksum mismatch! Actual: {data['actual']}")
            sys.exit(1)
        else:
            print(f"No checksum found to verify. Current: {data['actual']}")

    elif args.command == "write-checksum":
        write_checksum_command(args.file, args.output, tag=args.tag)
        print(f"Checksum written to {args.output}")

    elif args.command == "diff":
        if args.output:
            diff_visual_command(args.file1, args.file2, args.output, tag=args.tag)
            print(f"Visual diff saved to {args.output}")
        else:
            data = diff_command(args.file1, args.file2, tag=args.tag)
            import json

            # Convert sets to lists for JSON serialization
            serializable_data = {
                k: list(v) if isinstance(v, set) else v for k, v in data.items()
            }
            # Special handling for edge tuples
            for k in ["added_edges", "removed_edges", "modified_edges"]:
                serializable_data[k] = [f"{u}->{v}" for u, v in data[k]]

            print(json.dumps(serializable_data, indent=2))

    elif args.command == "serve":
        print(f"Serving {args.file} on http://127.0.0.1:{args.port}")
        # Note: serve_command needs update too
        from graphable.cli.commands.serve import serve_command

        serve_command(args.file, port=args.port, tag=args.tag)

    else:
        parser.print_help()


if __name__ == "__main__":
    run_bare()
