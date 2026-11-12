"""Check local href/src targets in EPUB XML documents; not an EPUB validator."""
import argparse
import json
import posixpath
import sys
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET
from zipfile import ZipFile, BadZipFile


def check(path):
    errors, skipped, references = [], [], 0
    with ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) > 10000 or sum(e.file_size for e in entries) > 100 * 1024 * 1024:
            raise ValueError('Archive exceeds this checker\'s 100 MB / 10,000 entry limit')
        names = [e.filename for e in entries]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate ZIP entry names')
        trees, ids = {}, {}
        for name in names:
            if not name.lower().endswith(('.xhtml', '.html', '.opf', '.ncx', '.svg', '.xml')):
                continue
            data = archive.read(name)
            # Fail closed for entity declarations; never resolve external entities.
            if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
                skipped.append({'file': name, 'reason': 'DTD/entity declaration not supported'})
                continue
            try:
                tree = ET.fromstring(data)
            except ET.ParseError:
                errors.append({'file': name, 'reason': 'XML parse error'})
                continue
            trees[name] = tree
            ids[name] = {e.get('id') or e.get('{http://www.w3.org/XML/1998/namespace}id') for e in tree.iter()}
        for name, tree in trees.items():
            for element in tree.iter():
                for attribute, href in element.attrib.items():
                    if attribute.rsplit('}', 1)[-1] not in ('href', 'src', 'full-path'):
                        continue
                    parsed = urlsplit(href)
                    if parsed.scheme or parsed.netloc:
                        continue  # No network requests or external URL validation.
                    base = '' if attribute == 'full-path' else posixpath.dirname(name)
                    target = posixpath.normpath(posixpath.join(base, unquote(parsed.path))) if parsed.path else name
                    references += 1
                    if target.startswith(('../', '/')) or target == '..' or target not in names:
                        errors.append({'file': name, 'target': href, 'reason': 'Missing or out-of-archive target'})
                    elif parsed.fragment and target in ids and unquote(parsed.fragment) not in ids[target]:
                        errors.append({'file': name, 'target': href, 'reason': 'Missing fragment ID'})
                    elif parsed.fragment and target not in ids:
                        skipped.append({'file': name, 'target': href, 'reason': 'Fragment target not parsed as XML'})
        return {'file': str(path), 'localReferencesChecked': references, 'errors': errors,
                'skipped': skipped, 'scope': 'XML href/src/full-path targets only; no CSS, rendering, language-quality or full EPUB conformance validation'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('epub')
    args = parser.parse_args()
    try:
        result = check(args.epub)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        sys.exit(1 if result['errors'] else 2 if result['skipped'] else 0)
    except (OSError, BadZipFile, ValueError, RuntimeError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=True))
        sys.exit(2)
