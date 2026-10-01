import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from lexer import LexicalError, MiniLexer, analyze


ROOT = Path(__file__).resolve().parents[1]


class LexerTests(unittest.TestCase):
    def get_output(self, source):
        output = StringIO()
        with redirect_stdout(output):
            symbol_table = analyze(source)
        return output.getvalue().splitlines(), symbol_table

    def test_document_example_exact_output(self):
        source = (ROOT / "inputs/valid_basic.txt").read_text()
        output, symbol_table = self.get_output(source)
        self.assertEqual(output, ["new identifier: A", "operator: +", "new identifier: B", "operator: -", "operator: *", "keyword: if", "keyword: then", "new identifier: id1", "new identifier: id2", 'identifier "id1" already in symbol table', 'string: "Hello World"'])
        self.assertEqual(symbol_table, {"A", "B", "id1", "id2"})

    def test_operators_and_punctuation(self):
        tokens = list(MiniLexer().tokenize("+ - * / = > >= < <= == ++ -- ( ) ;"))
        self.assertEqual([t.type for t in tokens], ["PLUS", "MINUS", "TIMES", "DIVIDE", "ASSIGN", "GT", "GE", "LT", "LE", "EQ", "INCREMENT", "DECREMENT", "LPAREN", "RPAREN", "SEMICOLON"])
        output, symbol_table = self.get_output("+ - * / = > >= < <= == ++ -- ( ) ;")
        self.assertEqual(output, ["operator: +", "operator: -", "operator: *", "operator: /", "operator: =", "operator: >", "operator: >=", "operator: <", "operator: <=", "operator: ==", "operator: ++", "operator: --", "left parenthesis: (", "right parenthesis: )", "semicolon: ;"])
        self.assertEqual(symbol_table, set())

    def test_adjacent_operators(self):
        self.assertEqual([t.value for t in MiniLexer().tokenize("A+++B-->=1")], ["A", "++", "+", "B", "--", ">=", "1"])

    def test_keywords_and_case(self):
        words = "if then else endif while do endwhile print newline read"
        self.assertTrue(all(t.type == "KEYWORD" for t in MiniLexer().tokenize(words)))
        output, symbol_table = self.get_output(words + " If IF Print READ iffy")
        self.assertEqual(symbol_table, {"If", "IF", "Print", "READ", "iffy"})
        self.assertEqual(output[:10], [f"keyword: {word}" for word in words.split()])

    def test_symbol_table_and_reset(self):
        output, symbol_table = self.get_output("A A a")
        self.assertEqual(output, ["new identifier: A", 'identifier "A" already in symbol table', "new identifier: a"])
        self.assertEqual(symbol_table, {"A", "a"})
        output, symbol_table = self.get_output("A")
        self.assertEqual(output, ["new identifier: A"])
        self.assertEqual(symbol_table, {"A"})

    def test_comments_and_line_numbers(self):
        tokens = list(MiniLexer().tokenize("A/* @ \n ** / \n */B// ignored\nC"))
        self.assertEqual([(t.value, t.lineno) for t in tokens], [("A", 1), ("B", 3), ("C", 4)])
        self.assertEqual(list(MiniLexer().tokenize("/**/ // eof")), [])
        self.assertEqual([token.value for token in MiniLexer().tokenize("A/**//**/B / C")], ["A", "B", "/", "C"])
        self.assertEqual([token.value for token in MiniLexer().tokenize("/* first */ A /* second */ B")], ["A", "B"])

    def test_strings_preserve_quotes_and_comment_markers(self):
        values = ['""', '"Hello World"', '"// /* @ */"', '"ภาษาไทย"']
        self.assertEqual([t.value for t in MiniLexer().tokenize(" ".join(values))], values)
        output, symbol_table = self.get_output("123 " + " ".join(values))
        self.assertEqual(output, ["integer: 123", *[f"string: {value}" for value in values]])
        self.assertEqual(symbol_table, set())

    def test_negative_integer_is_two_tokens(self):
        output, symbol_table = self.get_output("-10 0 12345")
        self.assertEqual(output, ["operator: -", "integer: 10", "integer: 0", "integer: 12345"])
        self.assertEqual(symbol_table, set())

    def test_errors(self):
        for source, character in [("1score", "1"), ("_score", "_"), ("student_name", "_"), ("@id", "@"), ("1.2", "."), ('"Hello', '"'), ('"Hello\nWorld"', '"'), ("/* unfinished", "/"), ("/*/", "/"), ("ไทย", "ไ"), ("١", "١")]:
            with self.subTest(source=source):
                with self.assertRaises(LexicalError) as caught:
                    self.get_output(source)
                self.assertEqual(caught.exception.character, character)

    def test_stops_before_following_identifier(self):
        output = StringIO()
        with redirect_stdout(output):
            with self.assertRaises(LexicalError):
                analyze("A @ B")
        self.assertEqual(output.getvalue().splitlines(), ["new identifier: A"])

    def test_whitespace_and_empty_input(self):
        output, symbol_table = self.get_output(" \r\n\t")
        self.assertEqual(output, [])
        self.assertEqual(symbol_table, set())

    def test_cli_examples_and_exit_codes(self):
        for path in sorted((ROOT / "inputs").glob("*.txt")):
            with self.subTest(path=path.name):
                result = subprocess.run([sys.executable, str(ROOT / "main.py"), str(path)], capture_output=True, text=True)
                invalid = path.name.startswith("invalid_")
                self.assertEqual(result.returncode, 1 if invalid else 0, result.stderr)
                self.assertEqual("Lexical error:" in result.stdout, invalid)
                self.assertEqual(result.stderr, "")
                if path.name == "invalid_lexical.txt":
                    self.assertEqual(result.stdout.splitlines(), ["new identifier: A", "Lexical error: unexpected character @"])
                if path.name == "valid_comments.txt":
                    self.assertEqual(result.stdout.splitlines(), ["keyword: read", "new identifier: A", "semicolon: ;", "keyword: read", "new identifier: B", "semicolon: ;", "keyword: if", 'identifier "A" already in symbol table', "operator: >=", 'identifier "B" already in symbol table', "keyword: then", "keyword: print", 'string: "A is greater"', "semicolon: ;", "keyword: print", "keyword: newline", "semicolon: ;", "keyword: endif", 'identifier "A" already in symbol table', "operator: ++", "semicolon: ;"])

    def test_unclosed_comment_stops_after_completed_comment(self):
        output = StringIO()
        with redirect_stdout(output):
            with self.assertRaises(LexicalError) as caught:
                analyze("A/* complete\ncomment */B /* unfinished\nC")
        self.assertEqual(output.getvalue().splitlines(), ["new identifier: A", "new identifier: B"])
        self.assertEqual(caught.exception.character, "/")
        self.assertEqual(caught.exception.lineno, 2)

    def test_utf8_bom_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = Path(temp_dir) / "source.txt"
            source_file.write_text('print "ภาษาไทย";', encoding="utf-8-sig")
            result = subprocess.run([sys.executable, str(ROOT / "main.py"), str(source_file)], capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ["keyword: print", 'string: "ภาษาไทย"', "semicolon: ;"])

    def test_missing_file(self):
        result = subprocess.run([sys.executable, str(ROOT / "main.py"), str(ROOT / "inputs" / "missing.txt")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Input error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
