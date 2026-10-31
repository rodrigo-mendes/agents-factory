#!/usr/bin/env python3
"""Positive (must block) and negative (must pass) samples for scripts/export_detectors.py.
Run: python scripts/tests/test_export_detectors.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import export_detectors as det  # noqa: E402

REAL_OCID = "ocid1.fnapp.oc1.sa-saopaulo-1." + "amaaaaaa543c4nyadf7booxbvvg6ernldcdbwrxahtw7w2jer3sfhp7ujjyq"

BLOCK = {
    "client": ["package com.brx.functions;", "BRX_SEND item=1", "tenant rgbu-rex-brxs-par1-mfcs",
               "host rex-npe.retail.example", "MAPFRE", "Accenture", '"customer_name": "Rodrigo Mendes"'],
    "email": ["ops@acme-real.com", "alarm_email = 'someone@corp.io'"],
    "ocid": [REAL_OCID, "ocid1.compartment.oc1.." + "aaaaaaaat3d6o3oron7jqrztl572jjrsdobf6bimutf57jirbzetc4magzja"],
    "ocir": ["gru.ocir.io/gr2o2hdgzoxw/app:1"],
    "host": ["https://lopiafgboojvw37sqyoxptl7t4.apigateway.sa-saopaulo-1.oci.customer-oci.com/v1",
             "https://idcs-" + "a23fd2fe5f18408c865bfc16a04cddb8.identity.oraclecloud.com/oauth2/v1/token"],
    "aws-account": ["arn:aws:iam::987654321098:role/x", "account_id = 987654321098"],
    "key": ["-----BEGIN RSA PRIVATE KEY-----", "ghp_" + "a" * 36, "AKIA" + "ABCDEFGHIJKLMNOP",
            "sk_live_" + "1234567890ab"],
    "personal-path": [r"C:\Users\r.dos.santos.mendes\x", "/Users/jsmith/project", "/home/jsmith/.oci"],
}

PASS = [
    "package com.example.functions;",
    "ops@example.com", "x@example.invalid", "jennyrosen@example.com", "alice@company.com",
    "ocid1.fnapp.oc1.<region>.<unique-id>", "ocid1.compartment.oc1..aaaa…",
    "gru.ocir.io/<namespace>/app", "gru.ocir.io/tenancyns/app", "gru.ocir.io/namespace/app",
    "https://docs.oracle.com/en-us/iaas/Content/Functions/home.htm",
    "https://idcs-<id>.identity.oraclecloud.com/oauth2/v1/token",
    "arn:aws:iam::111122223333:role/x", "arn:aws:iam::123456789012:role/x",
    "<PEM private key pasted here>",
    r"C:\Users\<user>\x", "/home/user/.oci/oci_api_key.pem", r"C:\Users\...", "/Users/.../x",
    "Quarkus 3.40.1.1", "550e8400-e29b-41d4-a716-446655440000",
    "/9j/4AAQSkZJRgABAgEASABIAAD/2wCEAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEB",
    "author: someone-else", "abrxq inside a random token",
]


class Detectors(unittest.TestCase):
    def test_every_detector_has_samples(self):
        self.assertEqual(set(BLOCK), set(det.DETECTORS))

    def test_positive_samples_block_with_the_right_detector(self):
        for name, samples in BLOCK.items():
            for s in samples:
                with self.subTest(detector=name, sample=s):
                    self.assertIn(name, {d for d, _ in det.scan_text(s)}, f"{s!r} should hit {name}")

    def test_negative_samples_pass(self):
        for s in PASS:
            with self.subTest(sample=s):
                self.assertEqual(det.scan_text(s), [], f"{s!r} should not be flagged")


if __name__ == "__main__":
    unittest.main(verbosity=1)
