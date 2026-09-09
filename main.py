import argparse
from pathlib import Path

from lexer import Analyzer, LexicalError


def main(argv=None):
    parser = argparse.ArgumentParser(description="Mini Lexical Analyzer (Python + SLY)")
    parser.add_argument("input", type=Path, help="UTF-8 source code file (.txt)")
    args = parser.parse_args(argv)
    try:
        source = args.input.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        parser.exit(2, f"Input error: {error}\n")

    try:
        for line in Analyzer().analyze(source):
            print(line)
    except LexicalError as error:
        print(error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
