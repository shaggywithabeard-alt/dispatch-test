# Lead list + first-touch emailer

Build a list of local businesses for a city, send each one a short intro email,
then call them a couple of days later. One CSV per city holds everything:
contact info, whether they were emailed, and your call notes.

Needs only Python 3.9+ (already on macOS; on Windows install it from python.org).
Nothing else to install.

## 1. Build a city's list

```sh
cd leadgen
python3 leadgen.py find --city "Panama City, Florida" --out lists/panama-city-fl.csv
python3 leadgen.py find --city "Los Angeles, California" --out lists/los-angeles.csv
python3 leadgen.py find --city "Memphis, Tennessee" --out lists/memphis.csv
python3 leadgen.py find --city "Phoenix, Arizona" --out lists/phoenix.csv
```

- Default categories are appointment and service businesses that lose money
  on missed calls: dentists, chiropractors, vets, salons, spas, auto repair,
  real estate, lawyers, plumbers, electricians, HVAC, roofers and restaurants.
  Run `python3 leadgen.py categories` for the full list, and pick your own with
  `--categories dentist,hvac,roofer`.
- Re-running `find` adds new businesses and never wipes your notes.
- Data comes from OpenStreetMap: free, and licensed so you may keep and reuse it.
  Coverage is good for names, phones and websites but thin on emails, so run step 2.
  For big cities, go one category at a time if the query times out.

### Adding businesses from anywhere else

If you have businesses from another source (a purchased list, a Google Maps
export, your own notes), put them in a CSV with a `business_name` column plus
any of `phone`, `email`, `website`, `address` and `category`. Then merge it in:

```sh
python3 leadgen.py import --file seeds/panama-city-fl-websearch.csv --list lists/panama-city-fl.csv --city "Panama City, Florida"
```

Businesses already on the list, matched by phone number or website, are
skipped, so importing twice or overlapping with `find` never creates
duplicates. `seeds/panama-city-fl-websearch.csv` is a starter list built by
web search; check a number if a call doesn't connect.

## 2. Find emails on their websites

```sh
python3 leadgen.py enrich --list lists/panama-city-fl.csv
```

This visits each business's website (home page, then /contact and /about) and
saves the best public email it finds. It prefers addresses on the business's
own domain, such as info@ or office@.

## 2b. Note what each business is missing

```sh
python3 leadgen.py audit --list lists/panama-city-fl.csv
```

This checks each business's website and writes what it lacks into the `gaps`
and `gap_notes` columns, which also appear on the call sheet:
- no website, or a site that won't load
- not secure (no HTTPS), or not built for phones
- no online booking (for appointment-based businesses)
- no chat or text-us option, so after-hours leads can only leave a voicemail
- phone number not tap-to-call; no contact form
- outdated site (old copyright year), very few photos
- no social links, no reviews shown

Other columns for your own findings:
- `research_notes`: anything found by hand or web search, such as hours,
  review counts or complaints.
- `after_hours_call`: call after closing time and write what happens:
  `voicemail`, `voicemail full`, `no answer`, `answering service` or `AI`. A
  business sending callers to voicemail is the strongest lead for an AI
  receptionist.

## 3. Send the first-touch email

1. Copy `config.example.env` to `config.env` and fill it in.
2. Edit `templates/first_touch.txt`. The text in `{curly braces}` is filled in
   for each business.
3. Preview it first. Without `--send`, nothing is sent:

```sh
python3 leadgen.py send --list lists/panama-city-fl.csv
python3 leadgen.py send --list lists/panama-city-fl.csv --send --limit 25
```

The script:
- Never emails the same business twice, and skips anyone marked `do_not_contact`.
- Waits 45–120 seconds between emails so it looks like a person sending.
- Always adds your company name, postal address and an unsubscribe line to the
  bottom, and won't run if those are missing.

### Sending through the Gmail connector (cloud sessions)

When direct mail-server access is blocked, the emails go out through the Gmail
connector instead. Claude writes the day's batch, sends each one, and records it:

```sh
python3 leadgen.py outbox --list lists/panama-city-fl.csv --limit 25   # writes outbox.json
python3 leadgen.py mark --list lists/panama-city-fl.csv --status sent <lead_id> ...
python3 leadgen.py mark --list lists/panama-city-fl.csv --status bounced --error "reason" <lead_id>
python3 leadgen.py mark --list lists/panama-city-fl.csv --status do_not_contact <lead_id>
```

The same rules apply as with `send`: nobody is emailed twice, do-not-contact is
respected, and the address and unsubscribe footer are always included.

## 4. Call them

```sh
python3 leadgen.py callsheet --list lists/panama-city-fl.csv
```

This writes `lists/panama-city-fl-calls.csv`: everyone emailed 2 or more days
ago who hasn't been called yet (change the gap with `--days`). Add
`--include-unemailed` to also include businesses that haven't been emailed yet.
Each row carries the gap and research notes, so you know the angle before
dialing.

Log each call in the **main** list in Excel or Google Sheets:
- `call_status`, e.g. `no answer`, `callback`, `meeting booked` or `not interested`
- `call_notes`
- `do_not_contact` = `yes` for anyone who asks to be left alone, and anyone
  who replies "unsubscribe"

`python3 leadgen.py stats --list lists/panama-city-fl.csv` shows how many
businesses you've emailed and called.

## Don't skip: keeping email out of spam and staying legal

**Deliverability**
- **Send from a separate domain**, e.g. `trybrandname.com` if your main site is
  `brandname.com`. If cold email gets flagged, your main domain stays clean.
- Set up SPF, DKIM and DMARC on that domain. Google Workspace walks you through
  it. Then send lightly for 2–3 weeks before any volume.
- Keep it to about **30–50 emails a day per inbox**. For more volume, add
  inboxes, not speed.
- Plain text, no attachments, no more than one link. The template already
  follows this.

**US law (CAN-SPAM) applies to B2B cold email.** You need:
- honest From and Subject lines
- your real postal address
- a clear way to opt out, honored within 10 business days

The script handles the address and opt-out line; honoring opt-outs is on you
(mark `do_not_contact`).

**Calls:** dial by hand. Robo-dialers and prerecorded messages to cell phones
need prior consent under the TCPA, and many small-business numbers are cell
phones. Florida has its own stricter version, the FTSA. Personal, hand-dialed
calls to businesses are fine.

**Outside the US**, e.g. Panama City, Panama, different rules apply, and the
template should be in Spanish.

## Tests

```sh
python3 -m unittest discover -s tests
```
