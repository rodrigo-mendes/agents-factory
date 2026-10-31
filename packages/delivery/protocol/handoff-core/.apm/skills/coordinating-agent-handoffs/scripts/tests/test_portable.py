import hashlib
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "portable.py")


def run(*args):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)


class TestPortable(unittest.TestCase):
    def test_now_is_utc_iso(self):
        r = run("now")
        self.assertEqual(r.returncode, 0)
        self.assertRegex(r.stdout.strip(), r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")

    def test_sha256_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "a.txt")
            with open(p, "wb") as fh:
                fh.write(b"abc")
            r = run("sha256", p)
            self.assertEqual(r.stdout.strip(), hashlib.sha256(b"abc").hexdigest())

    def test_dirhash_is_order_and_os_independent(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "s"))
            for rel, data in (("x.txt", b"a"), ("s/y.txt", b"b")):
                with open(os.path.join(d, rel), "wb") as fh:
                    fh.write(data)
            lines = "".join("%s  %s\n" % (hashlib.sha256(data).hexdigest(), rel)
                            for rel, data in (("s/y.txt", b"b"), ("x.txt", b"a")))
            expected = hashlib.sha256(lines.encode()).hexdigest()
            self.assertEqual(run("dirhash", d).stdout.strip(), expected)

    def test_usage_error(self):
        self.assertEqual(run("bogus").returncode, 2)
        self.assertEqual(run("dirhash", "/no/such/dir").returncode, 2)


if __name__ == "__main__":
    unittest.main()
