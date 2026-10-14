"""
validate-epub.py — EPUB 3.0 structural validator

Usage:
  python validate-epub.py <book.epub> [<book2.epub> ...]

Checks per file:
  - ZIP is readable (not corrupt)
  - mimetype is the first entry
  - mimetype is ZIP_STORED (uncompressed)
  - META-INF/container.xml exists with forward-slash path
  - No backslash paths in the archive
  - All .xhtml entries are well-formed XML

Exits 0 if all files PASS, exits 1 if any FAIL.
"""
import sys, zipfile
from xml.etree import ElementTree as ET

def validate(epub_path):
    checks = []

    try:
        zf = zipfile.ZipFile(epub_path, "r")
    except zipfile.BadZipFile as e:
        return False, [f"FAIL corrupt ZIP: {e}"]
    except FileNotFoundError:
        return False, [f"FAIL file not found: {epub_path}"]

    with zf:
        names = zf.namelist()

        # mimetype first
        if not names or names[0] != "mimetype":
            checks.append(f"FAIL mimetype is not first entry (got: {names[0] if names else 'empty'})")
        else:
            checks.append("OK   mimetype is first entry")

        # mimetype STORED
        try:
            mi = zf.getinfo("mimetype")
            if mi.compress_type != zipfile.ZIP_STORED:
                checks.append(f"FAIL mimetype compress_type={mi.compress_type} (expected ZIP_STORED=0)")
            else:
                checks.append("OK   mimetype is ZIP_STORED")
        except KeyError:
            checks.append("FAIL mimetype entry missing")

        # container.xml with forward slash
        if "META-INF/container.xml" not in names:
            checks.append("FAIL META-INF/container.xml not found (backslash path issue?)")
        else:
            checks.append("OK   META-INF/container.xml present")

        # no backslash paths
        bad = [n for n in names if "\\" in n]
        if bad:
            checks.append(f"FAIL {len(bad)} entries with backslash paths: {bad[:3]}")
        else:
            checks.append("OK   no backslash paths")

        # XHTML well-formedness
        xhtml_files = [n for n in names if n.endswith(".xhtml")]
        xhtml_errors = []
        for n in xhtml_files:
            try:
                ET.fromstring(zf.read(n))
            except ET.ParseError as e:
                xhtml_errors.append(f"{n}: {e}")
        if xhtml_errors:
            for err in xhtml_errors:
                checks.append(f"FAIL XHTML not well-formed: {err}")
        else:
            checks.append(f"OK   {len(xhtml_files)} XHTML file(s) well-formed")

    passed = all(c.startswith("OK") for c in checks)
    return passed, checks


def main():
    if len(sys.argv) < 2:
        print("Usage: validate-epub.py <book.epub> [<book2.epub> ...]")
        sys.exit(1)

    overall_pass = True
    for epub in sys.argv[1:]:
        passed, checks = validate(epub)
        status = "PASS" if passed else "FAIL"
        if not passed:
            overall_pass = False
        print(f"[{status}] {epub}")
        for c in checks:
            print(f"       {c}")

    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
