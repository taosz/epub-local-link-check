import json, subprocess, sys, tempfile, unittest, zipfile
from pathlib import Path

SCRIPT = Path(__file__).with_name('check_epub_links.py')

class LinkCheckTests(unittest.TestCase):
    def invoke(self, entries):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'book.epub'
            with zipfile.ZipFile(p, 'w') as z:
                for name, data in entries.items(): z.writestr(name, data)
            result = subprocess.run([sys.executable, str(SCRIPT), str(p)], capture_output=True, text=True)
            return result.returncode, json.loads(result.stdout)

    def test_links_and_fragment(self):
        code, out = self.invoke({'a.xhtml':'<html><a href="b.xhtml#chapter">next</a><a href="https://example.com">outside</a></html>', 'b.xhtml':'<html id="chapter"/>'})
        self.assertEqual(code, 0); self.assertEqual(out['localReferencesChecked'], 1)

    def test_missing_fragment_and_target(self):
        code, out = self.invoke({'a.xhtml':'<html><a href="b.xhtml#absent"/><a href="missing.xhtml"/></html>', 'b.xhtml':'<html id="present"/>'})
        self.assertEqual(code, 1); self.assertEqual(len(out['errors']), 2)

    def test_skipped_doctype_is_incomplete(self):
        code, out = self.invoke({'a.xhtml':'<!DOCTYPE html><html/>'})
        self.assertEqual(code, 2); self.assertEqual(len(out['skipped']), 1)

if __name__ == '__main__': unittest.main()
