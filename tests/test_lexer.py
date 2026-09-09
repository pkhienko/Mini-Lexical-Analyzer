import subprocess
import sys
import unittest
from pathlib import Path

from lexer import Analyzer, LexicalError, MiniLexer


ROOT = Path(__file__).resolve().parents[1]


class LexerTests(unittest.TestCase):
    def test_document_example_exact_output(self):
        source = (ROOT / "inputs/valid_basic.txt").read_text()
        self.assertEqual(list(Analyzer().analyze(source)), [
            "new identifier: A", "operator: +", "new identifier: B",
            "operator: -", "operator: *", "keyword: if", "keyword: then",
            "new identifier: id1", "new identifier: id2",
            'identifier "id1" already in symbol table', 'string: "Hello World"',
        ])

    def test_operators_and_punctuation(self):
        tokens = list(MiniLexer().tokenize("+ - * / = > >= < <= == ++ -- ( ) ;"))
        self.assertEqual([t.type for t in tokens], [
            "PLUS", "MINUS", "TIMES", "DIVIDE", "ASSIGN", "GT", "GE",
            "LT", "LE", "EQ", "INCREMENT", "DECREMENT", "LPAREN",
            "RPAREN", "SEMICOLON",
        ])

    def test_adjacent_operators(self):
        self.assertEqual([t.value for t in MiniLexer().tokenize("A+++B-->=1")],
                         ["A", "++", "+", "B", "--", ">=", "1"])

    def test_keywords_and_case(self):
        words = "if then else endif while do endwhile print newline read"
        self.assertTrue(all(t.type == "KEYWORD" for t in MiniLexer().tokenize(words)))
        analyzer = Analyzer()
        list(analyzer.analyze(words + " If IF Print READ iffy"))
        self.assertEqual(analyzer.symbol_table, {"If", "IF", "Print", "READ", "iffy"})

    def test_symbol_table_and_reset(self):
        analyzer = Analyzer()
        self.assertEqual(list(analyzer.analyze("A A a")), [
            "new identifier: A", 'identifier "A" already in symbol table',
            "new identifier: a",
        ])
        self.assertEqual(list(analyzer.analyze("A")), ["new identifier: A"])
        self.assertEqual(analyzer.symbol_table, {"A"})

    def test_comments_and_line_numbers(self):
        tokens = list(MiniLexer().tokenize("A/* @ \n ** / \n */B// ignored\nC"))
        self.assertEqual([(t.value, t.lineno) for t in tokens],
                         [("A", 1), ("B", 3), ("C", 4)])
        self.assertEqual(list(MiniLexer().tokenize("/**/ // eof")), [])

    def test_strings_preserve_quotes_and_comment_markers(self):
        values = ['""', '"Hello World"', '"// /* @ */"', '"ภาษาไทย"']
        self.assertEqual([t.value for t in MiniLexer().tokenize(" ".join(values))], values)

    def test_negative_integer_is_two_tokens(self):
        self.assertEqual(list(Analyzer().analyze("-10 0 12345")),
                         ["operator: -", "integer: 10", "integer: 0", "integer: 12345"])

    def test_errors(self):
        for source, character in [
            ("1score", "1"), ("_score", "_"), ("student_name", "_"),
            ("@id", "@"), ("1.2", "."), ('"Hello', '"'),
            ('"Hello\nWorld"', '"'), ("/* unfinished", "/"),
            ("/*/", "/"), ("ไทย", "ไ"), ("١", "١"),
        ]:
            with self.subTest(source=source):
                with self.assertRaises(LexicalError) as caught:
                    list(Analyzer().analyze(source))
                self.assertEqual(caught.exception.character, character)

    def test_stops_before_following_identifier(self):
        analyzer = Analyzer()
        output = analyzer.analyze("A @ B")
        self.assertEqual(next(output), "new identifier: A")
        with self.assertRaises(LexicalError):
            next(output)
        self.assertEqual(analyzer.symbol_table, {"A"})

    def test_whitespace_and_empty_input(self):
        self.assertEqual(list(Analyzer().analyze(" \r\n\t")), [])

    def test_cli_examples_and_exit_codes(self):
        for path in sorted((ROOT / "inputs").glob("*.txt")):
            with self.subTest(path=path.name):
                result = subprocess.run([sys.executable, str(ROOT / "main.py"), str(path)],
                                        capture_output=True, text=True)
                invalid = path.name.startswith("invalid_")
                self.assertEqual(result.returncode, 1 if invalid else 0, result.stderr)
                self.assertEqual("Lexical error:" in result.stdout, invalid)
                self.assertEqual(result.stderr, "")
                if path.name == "invalid_lexical.txt":
                    self.assertEqual(result.stdout.splitlines(), [
                        "new identifier: A", "Lexical error: unexpected character @",
                    ])

    def test_missing_file(self):
        result = subprocess.run([sys.executable, str(ROOT / "main.py"), str(ROOT / "inputs" / "missing.txt")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Input error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
