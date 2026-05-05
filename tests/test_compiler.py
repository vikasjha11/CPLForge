import os
import tempfile
import unittest

from cplc import compile_cpl, load_source


class CompilerSmokeTests(unittest.TestCase):
    def test_compile_generates_c_output(self):
        source = """
        int x = 1 + 2;
        print(x);
        """
        results = compile_cpl(
            source,
            filename="<test>",
            target="c",
            show_tokens=False,
            show_ast=False,
            show_ir=False,
            show_opt=False,
            show_symtable=False,
        )
        self.assertIn('c', results)
        self.assertIn('int main()', results['c'])
        self.assertIn('printf("%d\\n"', results['c'])

    def test_load_source_reads_file(self):
        with tempfile.NamedTemporaryFile('w', suffix='.cpl', delete=False, encoding='utf-8') as handle:
            handle.write('int a = 3;\n')
            temp_path = handle.name
        try:
            self.assertEqual(load_source(temp_path), 'int a = 3;\n')
        finally:
            os.remove(temp_path)


if __name__ == '__main__':
    unittest.main()
