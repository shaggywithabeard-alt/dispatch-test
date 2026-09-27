import csv
import datetime as dt
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import leadgen  # noqa: E402

CATS = ["dentist", "plumber"]

OVERPASS_ELEMENTS = [
    {"type": "node", "id": 1, "tags": {
        "name": "Bay Smiles Dental", "amenity": "dentist", "phone": "+1 850 555 0100;+1 850 555 0101",
        "website": "https://baysmiles.com", "addr:housenumber": "12", "addr:street": "Harrison Ave",
        "addr:city": "Panama City", "addr:state": "FL"}},
    {"type": "way", "id": 2, "tags": {
        "name": "Gulf Coast Plumbing", "craft": "plumber", "contact:email": "Info@GulfPlumb.com"}},
]

CONFIG = {
    "FROM_NAME": "Sam", "FROM_EMAIL": "sam@outreach.test", "COMPANY_NAME": "Acme LLC",
    "COMPANY_ADDRESS": "1 Main St, Panama City, FL", "FROM_PHONE": "555",
}


class TestFind(unittest.TestCase):
    def test_element_to_row(self):
        row = leadgen.element_to_row(OVERPASS_ELEMENTS[0], CATS, "Panama City, Florida")
        self.assertEqual(row["lead_id"], "osm-node-1")
        self.assertEqual(row["category"], "dentist")
        self.assertEqual(row["phone"], "+1 850 555 0100")
        self.assertEqual(row["address"], "12 Harrison Ave, Panama City, FL")
        row2 = leadgen.element_to_row(OVERPASS_ELEMENTS[1], CATS, "Panama City, Florida")
        self.assertEqual(row2["email"], "info@gulfplumb.com")
        self.assertEqual(row2["category"], "plumber")

    def test_merge_keeps_outreach_status(self):
        rows = []
        new = [leadgen.element_to_row(e, CATS, "PC") for e in OVERPASS_ELEMENTS]
        self.assertEqual(leadgen.merge_rows(rows, new), 2)
        rows[0]["email_status"] = "sent"
        rows[0]["call_notes"] = "call back Tue"
        self.assertEqual(leadgen.merge_rows(rows, new), 0)
        self.assertEqual(rows[0]["email_status"], "sent")
        self.assertEqual(rows[0]["call_notes"], "call back Tue")

    def test_query_uses_area(self):
        q = leadgen.build_overpass_query("area(id:3600001)", ["dentist"])
        self.assertIn('nwr["amenity"="dentist"]["name"](area.a);', q)
        q = leadgen.build_overpass_query("(1,2,3,4)", ["dentist"])
        self.assertIn('nwr["amenity"="dentist"]["name"](1,2,3,4);', q)


class TestEnrich(unittest.TestCase):
    def test_extract_and_pick(self):
        page = ('<a href="mailto:frontdesk%40baysmiles.com">Email</a> logo@2x.png '
                'jane@gmail.com support@wixpress.com info@baysmiles.com')
        emails = leadgen.extract_emails(page)
        self.assertNotIn("logo@2x.png", emails)
        self.assertNotIn("support@wixpress.com", emails)
        self.assertEqual(leadgen.pick_email(emails, "https://www.baysmiles.com/"), "frontdesk@baysmiles.com")
        self.assertEqual(leadgen.pick_email(["jane@gmail.com"], "baysmiles.com"), "jane@gmail.com")
        self.assertEqual(leadgen.pick_email([], "x.com"), "")


class TestSendAndCalls(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.list = os.path.join(self.dir, "pc.csv")
        rows = [dict.fromkeys(leadgen.FIELDS, "") for _ in range(4)]
        for i, r in enumerate(rows):
            r.update(lead_id=f"id{i}", business_name=f"Biz {i}", category="dentist",
                     city="Panama City, Florida", phone=f"555-000{i}", email=f"b{i}@biz{i}.com")
        rows[2]["do_not_contact"] = "yes"
        rows[3]["email_status"] = "sent"
        rows[3]["email_sent_at"] = "2020-01-01T00:00:00"
        leadgen.save_rows(self.list, rows)
        self.config = os.path.join(self.dir, "config.env")
        with open(self.config, "w") as f:
            f.write("\n".join(f"{k}={v}" for k, v in CONFIG.items()))
            f.write("\nSMTP_HOST=smtp.test\nSMTP_PORT=587\nSMTP_USER=u\nSMTP_PASSWORD=p\n")

    def test_message_has_compliance_footer(self):
        path = os.path.join(os.path.dirname(__file__), "..", "templates", "first_touch.txt")
        with open(path) as f:
            subject_t, body_t = leadgen.parse_template(f.read())
        row = leadgen.load_rows(self.list)[0]
        msg = leadgen.build_message(row, subject_t, body_t, CONFIG)
        self.assertEqual(msg["Subject"], "Quick question about missed calls at Biz 0")
        body = msg.get_content()
        self.assertIn("dentist businesses in Panama City", body)
        self.assertIn("1 Main St, Panama City, FL", body)
        self.assertIn("unsubscribe", body)
        self.assertIn("unsubscribe", msg["List-Unsubscribe"])

    def test_dry_run_sends_nothing(self):
        with mock.patch("smtplib.SMTP") as smtp:
            leadgen.main(["send", "--list", self.list, "--config", self.config])
        smtp.assert_not_called()
        self.assertEqual(leadgen.load_rows(self.list)[0]["email_status"], "")

    def test_send_skips_dnc_and_already_sent(self):
        with mock.patch("smtplib.SMTP") as smtp, mock.patch("time.sleep"):
            leadgen.main(["send", "--list", self.list, "--config", self.config, "--send"])
        server = smtp.return_value.__enter__.return_value
        sent_to = [c.args[0]["To"] for c in server.send_message.call_args_list]
        self.assertEqual(sent_to, ["b0@biz0.com", "b1@biz1.com"])
        rows = leadgen.load_rows(self.list)
        self.assertEqual([r["email_status"] for r in rows], ["sent", "sent", "", "sent"])
        # Second run: nothing left to send.
        with mock.patch("smtplib.SMTP") as smtp2:
            leadgen.main(["send", "--list", self.list, "--config", self.config, "--send"])
        smtp2.assert_not_called()

    def test_callsheet(self):
        out = os.path.join(self.dir, "calls.csv")
        leadgen.main(["callsheet", "--list", self.list, "--out", out])
        with open(out) as f:
            names = [r["business_name"] for r in csv.DictReader(f)]
        self.assertEqual(names, ["Biz 3"])  # emailed long ago, not called

    def test_missing_address_blocks_send(self):
        with open(self.config, "w") as f:
            f.write("FROM_NAME=a\nFROM_EMAIL=a@b.c\nCOMPANY_NAME=x\n")
        with self.assertRaises(SystemExit):
            leadgen.main(["send", "--list", self.list, "--config", self.config])


if __name__ == "__main__":
    unittest.main()
