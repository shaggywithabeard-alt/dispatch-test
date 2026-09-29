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

    def test_merge_dedupes_by_phone_and_website(self):
        rows = []
        leadgen.merge_rows(rows, [{"lead_id": "import-a", "business_name": "Bay Smiles",
                                   "phone": "(850) 555-0100", "website": ""}])
        osm = leadgen.element_to_row(OVERPASS_ELEMENTS[0], CATS, "PC")  # +1 850 555 0100
        self.assertEqual(leadgen.merge_rows(rows, [osm]), 0)
        self.assertEqual(rows[0]["website"], "https://baysmiles.com")  # blank filled in
        other = {"lead_id": "x", "business_name": "Bay Smiles 2", "phone": "",
                 "website": "http://www.baysmiles.com/contact"}
        self.assertEqual(leadgen.merge_rows(rows, [other]), 0)

    def test_import(self):
        d = tempfile.mkdtemp()
        src, lst = os.path.join(d, "in.csv"), os.path.join(d, "list.csv")
        with open(src, "w") as f:
            f.write("business_name,category,phone,email\nAcme HVAC,hvac,850-555-1234,A@Acme.com\n,,,\n")
        leadgen.main(["import", "--file", src, "--list", lst, "--city", "Panama City, Florida"])
        leadgen.main(["import", "--file", src, "--list", lst, "--city", "Panama City, Florida"])
        rows = leadgen.load_rows(lst)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["email"], "a@acme.com")

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


GOOD_SITE = ("<meta name='viewport' content='width=device-width'>"
             "<a href='tel:8505550100'>Call</a><form></form>"
             "<script src='https://widget.podium.com/x.js'></script>"
             "<a href='https://calendly.com/baysmiles'>Book online</a>"
             + "<img src='a.jpg'>" * 6 +
             "<a href='https://facebook.com/baysmiles'>fb</a> Testimonials &copy; 2026")
WEAK_SITE = "<html><img src='logo.png'> Call us 850-555-0100. Copyright 2019</html>"


class TestAudit(unittest.TestCase):
    def test_good_site_has_no_gaps(self):
        self.assertEqual(leadgen.audit_page("https://baysmiles.com/", GOOD_SITE, "dentist", 2026), [])

    def test_weak_site(self):
        gaps = leadgen.audit_page("http://oldsite.com/", WEAK_SITE, "dentist", 2026)
        self.assertEqual(gaps, ["no_https", "not_mobile_friendly", "no_online_booking",
                                "no_chat_or_text", "no_click_to_call", "no_contact_form",
                                "outdated_site", "few_photos", "no_social_links",
                                "no_reviews_shown"])
        self.assertIn("(copyright 2019)", leadgen.describe_gaps(gaps, WEAK_SITE))
        # Restaurants aren't flagged for lacking online booking.
        self.assertNotIn("no_online_booking", leadgen.audit_page("http://x.com", WEAK_SITE, "restaurant", 2026))

    def test_cmd_audit(self):
        d = tempfile.mkdtemp()
        lst = os.path.join(d, "l.csv")
        rows = [dict.fromkeys(leadgen.FIELDS, "") for _ in range(3)]
        rows[0].update(lead_id="a", business_name="No Site", category="hvac")
        rows[1].update(lead_id="b", business_name="Weak", category="dentist", website="oldsite.com")
        rows[2].update(lead_id="c", business_name="Down", category="dentist", website="down.com")
        leadgen.save_rows(lst, rows)

        def fake_fetch(url, timeout=None):
            if "down" in url:
                raise OSError("unreachable")
            return "http://oldsite.com/", WEAK_SITE

        with mock.patch.object(leadgen, "fetch", fake_fetch), mock.patch("time.sleep"):
            leadgen.main(["audit", "--list", lst])
        out = leadgen.load_rows(lst)
        self.assertEqual(out[0]["gaps"], "no_website")
        self.assertIn("no_online_booking", out[1]["gaps"])
        self.assertIn("No online booking", out[1]["gap_notes"])
        self.assertEqual(out[2]["gaps"], "site_down")
        self.assertTrue(all(r["audited_at"] for r in out))


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
        self.assertIn("dental businesses in Panama City", body)
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

    def test_outbox_then_mark(self):
        out = os.path.join(self.dir, "outbox.json")
        leadgen.main(["outbox", "--list", self.list, "--config", self.config, "--out", out])
        with open(out) as f:
            outbox = __import__("json").load(f)
        self.assertEqual([m["to"] for m in outbox], ["b0@biz0.com", "b1@biz1.com"])
        self.assertIn("unsubscribe", outbox[0]["body"])
        self.assertIn("1 Main St", outbox[0]["body"])
        leadgen.main(["mark", "--list", self.list, "--status", "sent", "id0"])
        leadgen.main(["mark", "--list", self.list, "--status", "bounced", "--error", "no such user", "id1"])
        rows = leadgen.load_rows(self.list)
        self.assertEqual(rows[0]["email_status"], "sent")
        self.assertTrue(rows[0]["email_sent_at"])
        self.assertEqual(rows[1]["email_status"], "bounced")
        leadgen.main(["outbox", "--list", self.list, "--config", self.config, "--out", out])
        with open(out) as f:
            self.assertEqual(__import__("json").load(f), [])
        with self.assertRaises(SystemExit):
            leadgen.main(["mark", "--list", self.list, "--status", "sent", "nope"])

    def test_callsheet(self):
        out = os.path.join(self.dir, "calls.csv")
        leadgen.main(["callsheet", "--list", self.list, "--out", out])
        with open(out) as f:
            names = [r["business_name"] for r in csv.DictReader(f)]
        self.assertEqual(names, ["Biz 3"])  # emailed long ago, not called
        leadgen.main(["callsheet", "--list", self.list, "--out", out, "--include-unemailed"])
        with open(out) as f:
            names = [r["business_name"] for r in csv.DictReader(f)]
        self.assertEqual(names, ["Biz 3", "Biz 0", "Biz 1"])  # DNC Biz 2 never listed

    def test_missing_address_blocks_send(self):
        with open(self.config, "w") as f:
            f.write("FROM_NAME=a\nFROM_EMAIL=a@b.c\nCOMPANY_NAME=x\n")
        with self.assertRaises(SystemExit):
            leadgen.main(["send", "--list", self.list, "--config", self.config])


if __name__ == "__main__":
    unittest.main()
