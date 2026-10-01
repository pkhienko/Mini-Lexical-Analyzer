import sys
from lexer import LexicalError, analyze

def main():
    if len(sys.argv) != 2:
        print("Error: Please provide one input file")
        print("Usage: py main.py <input_file>")
        return 1

    filename = sys.argv[1]

    try:
        with open(filename, "r", encoding="utf-8-sig") as file:
            source = file.read()
    except FileNotFoundError:
        print("Error: File not found")
        return 1
    except (OSError, UnicodeError) as error:
        print(f"Error: Unable to read file: {error}")
        return 1

    try:
        analyze(source)
    except LexicalError as error:
        print(error)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())