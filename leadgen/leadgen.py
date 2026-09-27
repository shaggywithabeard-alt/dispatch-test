#!/usr/bin/env python3
"""Local-business lead list builder, first-touch emailer, and call sheet.

Workflow (one CSV per city is the single source of truth):

  1. find      Pull businesses for a city from OpenStreetMap into a CSV.
  2. enrich    Visit each business website and pick up a public contact email.
  3. send      Send the first-touch cold email (dry run unless --send).
  4. callsheet Export who to call next: emailed N+ days ago, not yet called.

Open the CSV in Excel / Google Sheets to log calls (call_status, call_notes),
and mark anyone who asks to be left alone with do_not_contact = yes.

Standard library only. Run `python3 leadgen.py <command> -h` for options.
"""

import argparse
import csv
import datetime as dt
import html
import json
import os
import random
import re
import smtplib
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

HERE = os.path.dirname(os.path.abspath(__file__))
USER_AGENT = "leadgen/1.0 (local business outreach list builder)"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

FIELDS = [
    "lead_id", "business_name", "category", "phone", "email", "website",
    "address", "city", "source",
    "email_status", "email_sent_at", "email_error",
    "call_status", "call_notes", "do_not_contact",
]

# Friendly category name -> OpenStreetMap tag filters. Weighted toward
# appointment/service businesses that lose money on missed calls.
CATEGORIES = {
    "dentist": [("amenity", "dentist")],
    "doctor": [("amenity", "doctors"), ("amenity", "clinic")],
    "chiropractor": [("healthcare", "chiropractor")],
    "physical_therapy": [("healthcare", "physiotherapist")],
    "veterinarian": [("amenity", "veterinary")],
    "hair_salon": [("shop", "hairdresser")],
    "beauty_spa": [("shop", "beauty"), ("leisure", "spa")],
    "gym": [("leisure", "fitness_centre")],
    "restaurant": [("amenity", "restaurant")],
    "cafe": [("amenity", "cafe")],
    "bar": [("amenity", "bar"), ("amenity", "pub")],
    "hotel": [("tourism", "hotel"), ("tourism", "motel")],
    "auto_repair": [("shop", "car_repair"), ("shop", "tyres")],
    "car_dealer": [("shop", "car")],
    "real_estate": [("office", "estate_agent")],
    "property_management": [("office", "property_management")],
    "lawyer": [("office", "lawyer")],
    "accountant": [("office", "accountant"), ("office", "tax_advisor")],
    "insurance": [("office", "insurance")],
    "plumber": [("craft", "plumber")],
    "electrician": [("craft", "electrician")],
    "hvac": [("craft", "hvac")],
    "roofer": [("craft", "roofer")],
    "contractor": [("craft", "builder"), ("office", "construction_company")],
}

DEFAULT_CATEGORIES = [
    "dentist", "chiropractor", "veterinarian", "hair_salon", "beauty_spa",
    "auto_repair", "real_estate", "lawyer", "plumber", "electrician", "hvac",
    "roofer", "restaurant",
]


# ---------------------------------------------------------------- CSV store

def load_rows(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for field in FIELDS:
            row.setdefault(field, "")
    return rows


def save_rows(path, rows):
    """Write atomically so a crash mid-send never corrupts the list."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".csv.tmp")
    with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, path)


def is_yes(value):
    return str(value).strip().lower() in {"yes", "y", "true", "1", "x"}


# ---------------------------------------------------------------- HTTP

def http_get(url, params=None, data=None, timeout=60):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read(2_000_000).decode(charset, errors="replace")


# ---------------------------------------------------------------- find

def geocode_area(city):
    """Return (overpass area selector, display name) for a city name."""
    results = json.loads(http_get(NOMINATIM_URL, {
        "q": city, "format": "json", "limit": 5,
    }))
    if not results:
        sys.exit(f"Could not find '{city}'. Try adding the state/country, "
                 f"e.g. 'Panama City, Florida' or 'Panama City, Panama'.")
    for r in results:
        if r.get("osm_type") == "relation":
            return f"area(id:{3600000000 + int(r['osm_id'])})", r["display_name"]
    r = results[0]
    south, north, west, east = r["boundingbox"]
    return f"({south},{west},{north},{east})", r["display_name"]


def build_overpass_query(area_selector, categories):
    if area_selector.startswith("area("):
        head = f"{area_selector}->.a;\n"
        scope = "(area.a)"
    else:
        head = ""
        scope = area_selector
    parts = []
    for cat in categories:
        for key, value in CATEGORIES[cat]:
            parts.append(f'  nwr["{key}"="{value}"]["name"]{scope};')
    return ("[out:json][timeout:180];\n" + head + "(\n" + "\n".join(parts)
            + "\n);\nout center tags;")


def category_of(tags, categories):
    for cat in categories:
        for key, value in CATEGORIES[cat]:
            if tags.get(key) == value:
                return cat
    return ""


def first_tag(tags, *keys):
    for key in keys:
        if tags.get(key):
            # OSM allows "a;b" for multiple values; keep the first.
            return tags[key].split(";")[0].strip()
    return ""


def element_to_row(element, categories, city):
    tags = element.get("tags", {})
    street = " ".join(filter(None, [tags.get("addr:housenumber"), tags.get("addr:street")]))
    address = ", ".join(filter(None, [
        street, tags.get("addr:city"), tags.get("addr:state"), tags.get("addr:postcode"),
    ]))
    return {
        "lead_id": f"osm-{element['type']}-{element['id']}",
        "business_name": tags.get("name", "").strip(),
        "category": category_of(tags, categories),
        "phone": first_tag(tags, "phone", "contact:phone", "contact:mobile"),
        "email": first_tag(tags, "email", "contact:email").lower(),
        "website": first_tag(tags, "website", "contact:website", "url"),
        "address": address,
        "city": city,
        "source": "OpenStreetMap (ODbL)",
    }


def merge_rows(existing, new_rows):
    """Add new leads; fill blanks on known ones; never touch outreach status."""
    by_id = {r["lead_id"]: r for r in existing}
    added = 0
    for new in new_rows:
        old = by_id.get(new["lead_id"])
        if old is None:
            row = {f: "" for f in FIELDS}
            row.update(new)
            existing.append(row)
            by_id[row["lead_id"]] = row
            added += 1
        else:
            for key in ("phone", "email", "website", "address", "category"):
                if not old.get(key) and new.get(key):
                    old[key] = new[key]
    return added


def cmd_find(args):
    categories = args.categories.split(",") if args.categories else DEFAULT_CATEGORIES
    unknown = [c for c in categories if c not in CATEGORIES]
    if unknown:
        sys.exit(f"Unknown categories: {', '.join(unknown)}\n"
                 f"Available: {', '.join(sorted(CATEGORIES))}")
    area, name = geocode_area(args.city)
    print(f"Searching {name}")
    query = build_overpass_query(area, categories)
    data = json.loads(http_get(OVERPASS_URL, data={"data": query}, timeout=240))
    new_rows = [element_to_row(e, categories, args.city) for e in data.get("elements", [])]
    new_rows = [r for r in new_rows if r["business_name"]]
    if args.require_contact:
        new_rows = [r for r in new_rows if r["phone"] or r["website"] or r["email"]]
    rows = load_rows(args.out)
    added = merge_rows(rows, new_rows)
    save_rows(args.out, rows)
    with_phone = sum(1 for r in rows if r["phone"])
    with_site = sum(1 for r in rows if r["website"])
    with_email = sum(1 for r in rows if r["email"])
    print(f"Found {len(new_rows)} businesses, {added} new. List now has {len(rows)}: "
          f"{with_phone} with phone, {with_site} with website, {with_email} with email.")
    print(f"Saved to {args.out}")
    print("Next: python3 leadgen.py enrich --list " + args.out)


# ---------------------------------------------------------------- enrich

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
MAILTO_RE = re.compile(r"mailto:([^\"'?>\s]+)", re.I)
JUNK_EMAIL = re.compile(
    r"(\.(png|jpe?g|gif|svg|webp|css|js)$)|example\.|sentry|wixpress|"
    r"domain\.com|yourname|@email\.com|godaddy|squarespace|noreply|no-reply", re.I)
PREFERRED_PREFIXES = ("info", "contact", "hello", "office", "admin", "appointments",
                      "frontdesk", "reception", "sales", "service")


def domain_of(url):
    host = urllib.parse.urlparse(url if "//" in url else "http://" + url).hostname or ""
    return host.lower().removeprefix("www.")


def extract_emails(page):
    page = html.unescape(page)
    found = [urllib.parse.unquote(m) for m in MAILTO_RE.findall(page)]
    found += EMAIL_RE.findall(page)
    seen, out = set(), []
    for email in found:
        email = email.strip(".,;:").lower()
        if email not in seen and not JUNK_EMAIL.search(email):
            seen.add(email)
            out.append(email)
    return out


def pick_email(emails, website):
    """Prefer an address on the business's own domain, then a role inbox."""
    if not emails:
        return ""
    site = domain_of(website)

    def score(email):
        local, _, dom = email.partition("@")
        return (0 if site and (dom == site or dom.endswith("." + site)) else 1,
                0 if local.startswith(PREFERRED_PREFIXES) else 1)

    return sorted(emails, key=score)[0]


def cmd_enrich(args):
    rows = load_rows(args.list)
    todo = [r for r in rows if r["website"] and not r["email"] and not is_yes(r["do_not_contact"])]
    if args.limit:
        todo = todo[: args.limit]
    print(f"Checking {len(todo)} websites for a contact email...")
    found = 0
    for i, row in enumerate(todo, 1):
        base = row["website"] if "//" in row["website"] else "http://" + row["website"]
        emails = []
        for path in ("", "/contact", "/contact-us", "/about"):
            try:
                emails += extract_emails(http_get(urllib.parse.urljoin(base, path), timeout=15))
            except (urllib.error.URLError, OSError, ValueError):
                continue
            if emails:
                break
        email = pick_email(emails, row["website"])
        if email:
            row["email"] = email
            found += 1
        print(f"  [{i}/{len(todo)}] {row['business_name']}: {email or '-'}")
        if i % 10 == 0:
            save_rows(args.list, rows)
        time.sleep(args.delay)
    save_rows(args.list, rows)
    print(f"Added {found} emails. Saved to {args.list}")


# ---------------------------------------------------------------- send

def load_config(path):
    config = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    config[key.strip()] = value.strip().strip('"').strip("'")
    for key, value in os.environ.items():
        if key.startswith("LEADGEN_"):
            config[key.removeprefix("LEADGEN_")] = value
    return config


REQUIRED_CONFIG = ["FROM_NAME", "FROM_EMAIL", "COMPANY_NAME", "COMPANY_ADDRESS"]
REQUIRED_SMTP = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD"]


def parse_template(text):
    """First line 'Subject: ...', blank line, then the body."""
    first, _, body = text.partition("\n")
    if not first.lower().startswith("subject:"):
        sys.exit("Template must start with a 'Subject: ...' line.")
    return first[len("subject:"):].strip(), body.lstrip("\n")


class _Blank(dict):
    def __missing__(self, key):
        return ""


def render(template, row, config):
    values = _Blank(config)
    values.update({
        "business_name": row["business_name"],
        "category": row["category"].replace("_", " "),
        "city": row["city"].split(",")[0].strip(),
    })
    return template.format_map(values)


def compliance_footer(config):
    # CAN-SPAM: identify the sender, include a valid postal address, and give
    # a working way to opt out. Always appended; the template can't drop it.
    return ("\n\n--\n"
            f"{config['COMPANY_NAME']}, {config['COMPANY_ADDRESS']}\n"
            "Not interested? Reply \"unsubscribe\" and we won't email you again.")


def eligible_for_email(row):
    return (row["email"] and not row["email_status"]
            and not is_yes(row["do_not_contact"]))


def build_message(row, subject_t, body_t, config):
    msg = EmailMessage()
    msg["From"] = formataddr((config["FROM_NAME"], config["FROM_EMAIL"]))
    msg["To"] = row["email"]
    if config.get("REPLY_TO"):
        msg["Reply-To"] = config["REPLY_TO"]
    msg["Subject"] = render(subject_t, row, config)
    msg["Message-ID"] = make_msgid(domain=config["FROM_EMAIL"].split("@")[-1])
    msg["List-Unsubscribe"] = f"<mailto:{config.get('REPLY_TO') or config['FROM_EMAIL']}?subject=unsubscribe>"
    msg.set_content(render(body_t, row, config).rstrip() + compliance_footer(config))
    return msg


def cmd_send(args):
    config = load_config(args.config)
    missing = [k for k in REQUIRED_CONFIG + (REQUIRED_SMTP if args.send else []) if not config.get(k)]
    if missing:
        sys.exit(f"Missing in {args.config}: {', '.join(missing)} (see config.example.env)")
    with open(args.template, encoding="utf-8") as f:
        subject_t, body_t = parse_template(f.read())
    rows = load_rows(args.list)
    queue = [r for r in rows if eligible_for_email(r)]
    if args.category:
        queue = [r for r in queue if r["category"] == args.category]
    queue = queue[: args.limit]
    if not queue:
        print("Nobody left to email (needs an email, not yet emailed, not do-not-contact).")
        return

    if not args.send:
        print(f"DRY RUN: {len(queue)} emails would go out. First one:\n")
        print(build_message(queue[0], subject_t, body_t, config).as_string())
        print("\nRecipients:")
        for r in queue:
            print(f"  {r['business_name']} <{r['email']}>")
        print("\nAdd --send to actually send.")
        return

    port = int(config["SMTP_PORT"])
    smtp_cls = smtplib.SMTP_SSL if port == 465 else smtplib.SMTP
    sent = 0
    with smtp_cls(config["SMTP_HOST"], port, timeout=60) as smtp:
        if port != 465:
            smtp.starttls()
        smtp.login(config["SMTP_USER"], config["SMTP_PASSWORD"])
        for i, row in enumerate(queue, 1):
            try:
                smtp.send_message(build_message(row, subject_t, body_t, config))
                row["email_status"] = "sent"
                row["email_sent_at"] = dt.datetime.now().isoformat(timespec="seconds")
                row["email_error"] = ""
                sent += 1
                print(f"  [{i}/{len(queue)}] sent -> {row['business_name']} <{row['email']}>")
            except smtplib.SMTPRecipientsRefused as e:
                row["email_status"] = "bounced"
                row["email_error"] = str(e)[:200]
                print(f"  [{i}/{len(queue)}] refused -> {row['email']}")
            save_rows(args.list, rows)
            if i < len(queue):
                time.sleep(random.uniform(args.min_delay, args.max_delay))
    print(f"Sent {sent}. Saved to {args.list}")


# ---------------------------------------------------------------- callsheet

CALL_FIELDS = ["business_name", "category", "phone", "email", "website", "address",
               "email_sent_at", "call_status", "call_notes"]


def cmd_callsheet(args):
    rows = load_rows(args.list)
    cutoff = dt.datetime.now() - dt.timedelta(days=args.days)
    due = []
    for r in rows:
        if not r["phone"] or r["call_status"] or is_yes(r["do_not_contact"]):
            continue
        if r["email_status"] == "sent":
            if dt.datetime.fromisoformat(r["email_sent_at"]) <= cutoff:
                due.append(r)
        elif args.include_unemailed and not r["email"]:
            due.append(r)
    due.sort(key=lambda r: r["email_sent_at"] or "9999")
    out = args.out or args.list.replace(".csv", "") + "-calls.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CALL_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(due)
    print(f"{len(due)} businesses to call. Saved to {out}")
    print("Log results back in the main list (call_status, call_notes, do_not_contact).")


# ---------------------------------------------------------------- stats

def cmd_stats(args):
    rows = load_rows(args.list)
    count = lambda pred: sum(1 for r in rows if pred(r))
    print(f"{args.list}: {len(rows)} businesses")
    print(f"  with phone     {count(lambda r: r['phone'])}")
    print(f"  with email     {count(lambda r: r['email'])}")
    print(f"  emailed        {count(lambda r: r['email_status'] == 'sent')}")
    print(f"  bounced        {count(lambda r: r['email_status'] == 'bounced')}")
    print(f"  called         {count(lambda r: r['call_status'])}")
    print(f"  do not contact {count(lambda r: is_yes(r['do_not_contact']))}")
    by_cat = {}
    for r in rows:
        by_cat[r["category"] or "other"] = by_cat.get(r["category"] or "other", 0) + 1
    for cat, n in sorted(by_cat.items(), key=lambda kv: -kv[1]):
        print(f"    {cat:<20}{n}")


# ---------------------------------------------------------------- CLI

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    f = sub.add_parser("find", help="build/extend a city's lead list from OpenStreetMap")
    f.add_argument("--city", required=True, help='e.g. "Panama City, Florida"')
    f.add_argument("--categories", help="comma-separated; run the `categories` command to see them")
    f.add_argument("--out", required=True, help="CSV path, e.g. lists/panama-city-fl.csv")
    f.add_argument("--require-contact", action="store_true",
                   help="skip businesses with no phone, website, or email")
    f.set_defaults(func=cmd_find)

    e = sub.add_parser("enrich", help="find contact emails on business websites")
    e.add_argument("--list", required=True)
    e.add_argument("--limit", type=int, default=0)
    e.add_argument("--delay", type=float, default=1.0, help="seconds between sites")
    e.set_defaults(func=cmd_enrich)

    s = sub.add_parser("send", help="send the first-touch email (dry run by default)")
    s.add_argument("--list", required=True)
    s.add_argument("--template", default=os.path.join(HERE, "templates", "first_touch.txt"))
    s.add_argument("--config", default=os.path.join(HERE, "config.env"))
    s.add_argument("--limit", type=int, default=25, help="max emails this run (default 25)")
    s.add_argument("--category", help="only this category")
    s.add_argument("--min-delay", type=float, default=45)
    s.add_argument("--max-delay", type=float, default=120)
    s.add_argument("--send", action="store_true", help="actually send")
    s.set_defaults(func=cmd_send)

    c = sub.add_parser("callsheet", help="export who to call next")
    c.add_argument("--list", required=True)
    c.add_argument("--days", type=int, default=2, help="call N+ days after the email")
    c.add_argument("--include-unemailed", action="store_true",
                   help="also include businesses with a phone but no email")
    c.add_argument("--out")
    c.set_defaults(func=cmd_callsheet)

    st = sub.add_parser("stats", help="summary of a list")
    st.add_argument("--list", required=True)
    st.set_defaults(func=cmd_stats)

    lc = sub.add_parser("categories", help="show available categories")
    lc.set_defaults(func=lambda a: print("\n".join(
        f"{k:<20}{'(default)' if k in DEFAULT_CATEGORIES else ''}" for k in sorted(CATEGORIES))))

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
