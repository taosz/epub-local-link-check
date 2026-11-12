# EPUB local link check

Check links within an EPUB after editing or translation, without uploading the book. This small Python utility checks XML `href`, `src` and package `full-path` targets and, where the destination is parsed XML, fragment IDs. It does not compare two files: run it on each file separately.

## Run

Requires Python 3.10+; standard library only.

```shell
python check_epub_links.py original.epub
python check_epub_links.py translation.epub
```

JSON output includes the number of local references checked, errors and checks skipped. Exit code **0** means no errors or skips within the stated scope; **1** means a missing target, missing checked fragment, or malformed XML; **2** means an incomplete check or unreadable archive. If both errors and skips occur the exit code is 1: inspect both arrays. Reports can contain file paths and internal link targets; treat them as potentially sensitive before sharing. Archives are not extracted and the script makes no network requests.

Limits: this is not [EPUBCheck](https://www.w3.org/publishing/epubcheck/), a security scanner, accessibility assessment, renderer or translation quality check. It does not check CSS references, external URLs, navigation order, or visual appearance. XML documents with DTD or entity declarations are skipped, as are fragment destinations that could not be parsed as XML; these yield an incomplete result. EPUB HTML must be well-formed XML for this checker. Archives are limited to 10,000 entries and 100 MiB declared uncompressed size. Do not use it to establish that an untrusted file is safe. Check both books in an EPUB reader and have a qualified reader review meaning, numbers and names.

## Try it on a real example

Scanfile published a short fictional [English source](https://scanfile.online/samples/epub/en-pt-br/reading-garden.en.epub) and its [Brazilian Portuguese translation](https://scanfile.online/samples/epub/en-pt-br/reading-garden.pt-br.epub). Download them and run the commands above with their actual filenames, then follow chapter, footnote and return links in an EPUB reader. The result is an unedited machine translation and has not had independent editorial review. One small example cannot establish general translation quality or preservation.

## Relationship and license

This utility is published by the team behind [Scanfile](https://scanfile.online/tools/epub-book-translator), a commercial EPUB translation service. The checker works independently and does not translate, require an account or upload a book. Translation on Scanfile is a separate online service; review its terms and pricing before uploading. This documentation was prepared with AI assistance. Code is MIT licensed; the linked examples are not included under the code license.

## Use in GitHub Actions

For a project that builds an EPUB on a GitHub-hosted Linux runner, run the checker after your build step. The following example assumes your build has produced `book.epub` in the workspace. Pin this action to a reviewed commit SHA in a production workflow.

```yaml
name: Check ebook links
on: [push, pull_request]
permissions:
  contents: read
jobs:
  links:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # Add your own EPUB build step here.
      - uses: taosz/epub-local-link-check@v0.1.0
        with:
          epub-path: book.epub
```

The action fails when the checker reports errors **or incomplete checks**. The report is printed in the runner log and can contain internal paths and link targets. Anyone with access to those logs may see them; avoid running this on confidential books without assessing your CI provider and repository access. This action sends no file to Scanfile; checkout and GitHub-hosted runners are separate services. Run EPUBCheck and reader/linguistic review independently.
