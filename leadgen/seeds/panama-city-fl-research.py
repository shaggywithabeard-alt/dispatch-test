"""Web-search research (2026-09-27) on Panama City leads that had no website
on file. Fills blanks and adds research_notes. Run once:
    python3 seeds/panama-city-fl-research.py lists/panama-city-fl.csv
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import leadgen  # noqa: E402

NO_SITE = "no_website"

# name: (updates, research note, no website found?)
RESEARCH = {
    "Bush Air Conditioning": ({"website": ""},
        "No website of its own found, only directory listings. BBB says it merged with Whitehead Plumbing into Whitehead Plumbing & Air Conditioning; alt phone (850) 250-2362. Est. 1969, 5 stars on YP. Ask who handles calls now.", True),
    "Personal Attention Dental Center": ({"website": "myfundentist.com", "address": "5701 Hickory St, Panama City, FL 32404"},
        "Strong reviews (4.9 stars, 1,849 on Birdeye), so it already uses review software. Pitch after-hours answering and follow-ups, not reviews.", False),
    "Harrison Dental Associates": ({"phone": "(850) 763-6782", "website": "harrisondental.com", "address": "1601 Harrison Ave, Panama City, FL 32405"},
        "Open Mon-Thu 8-4:30, CLOSED Fri-Sun: calls go unanswered 3 days a week. Online 'appointment request' form only, no real-time booking.", False),
    "Kennon Dental Associates": ({"phone": "(850) 769-1034", "website": "kennondental.com", "address": "2309-B St Andrews Blvd, Panama City, FL 32405"},
        "Family-owned. Open Mon-Thu 8-5, CLOSED Fri-Sun: 3 days a week with no one answering.", False),
    "Baldwin Family Dental": ({"phone": "(850) 215-0128", "website": "baldwinfamilydental.com", "address": "528 W Baldwin Rd Unit B, Panama City, FL 32405"},
        "Open Mon-Thu 8-5, Fri 8-2, closed weekends. Only 8 reviews found on Healthgrades.", False),
    "Panama City Smiles": ({"phone": "(850) 763-8788", "website": "panamacitysmiles.com", "address": "1022 Harrison Ave, Panama City, FL 32401"},
        "Open Mon-Fri 8-5, closed weekends. 35 Yelp reviews. Advertises emergency dental care but no one answers after hours.", False),
    "Cove Dental Care": ({"phone": "(850) 769-1710", "website": "covedentalcare.com", "address": "406 N Cove Blvd, Panama City, FL 32401"},
        "Open Mon-Thu 8-5, CLOSED Fri-Sun.", False),
    "Bay Dental Center": ({"phone": "(850) 785-5502", "website": "baydentalcenter.com", "email": "baydentalc@yahoo.com", "address": "45 E Beach Dr, Panama City, FL 32401"},
        "Uses a Yahoo email address (unprofessional). Site is a Hibu template. Open Mon-Fri 8-5, closed weekends. Second office in Santa Rosa Beach.", False),
    "Jimmy Lumley Plumbing": ({},
        "No website found. Open Mon-Fri 7:30-4, CLOSED weekends, so weekend plumbing emergencies go unanswered. In business since 1979, top 5% on BuildZoom, 5 stars on YP.", True),
    "West End Plumbing Contractors": ({},
        "No website found. Says it's open 24/7 but only 6 Yelp reviews (4 stars), and Nextdoor complaints about missed appointments and poor communication. Family-owned since 1996.", True),
    "Bowden's Plumbing & Electrical": ({"address": "7426 Joanna Ln, Panama City, FL 32409"},
        "No website found. BBB A+ since 2005, in business since 1985. Reviews complain they 'never show up when they say' (reminders and follow-up would fix this).", True),
    "Certified Roofing Solutions": ({"website": "certifiedroofingsolutionsllc.com", "address": "3129 Thomas Dr, Panama City, FL 32408"},
        "Strong reviews (4.8 stars, 236 on Birdeye), BBB Torch Award 2022. Few obvious gaps; pitch after-hours answering for storm-season call spikes.", False),
    "Andrews Roofing and Construction": ({"website": "andrewsroofingpanamacity.com", "address": "2812 St Andrews Blvd, Panama City, FL 32405"},
        "BBB A+, family business, 4 generations. Reviews praise fast estimates, so speed-to-lead is their selling point; an AI receptionist protects it.", False),
    "Greg's Roofing of Bay County": ({},
        "No website found, only directory listings. 4.6 stars on Angi, 25+ years. The owner (Greg) personally handles calls and emergencies, so he misses calls while on roofs.", True),
    "Kenny Strange Electric": ({"website": "kselectricusa.com"},
        "Says it's open 24/7. 4.1-4.3 stars (33 and 59 reviews on Birdeye) with one 'worst customer service' complaint. 30+ years in business.", False),
    "Meyers Electric": ({"website": "meyerselectric.net"},
        "Open Mon-Fri 7:30-5, closed weekends. 84 Google reviews, 4.0 stars on Yelp (11).", False),
    "Chiropractic Care of Panama City": ({"website": "chirocarepc.com", "email": "drlynda@chirocarepc.com"},
        "Already has online booking (Jane app). Odd hours: Mon, Tue, Thu 8-5 and Sat 8-1, CLOSED Wed and Fri. New Facebook page, so ownership may have changed recently.", False),
    "Bauman Chiropractic": ({"website": "baumanchiropractic.net"},
        "Large practice: 3 chiropractors and 8 massage therapists, about 70 years old. Open Mon-Thu 8-5, CLOSED Fri-Sun. High call volume, so good fit for an AI receptionist.", False),
    "Panama City Chiropractic": ({"phone": "(850) 784-9355"},
        "Very few reviews online. Its website panamacitychiropractic.com also shows 'Chiropractic Worx' (same business? confirm on the call).", False),
    "Panama City Laser & MedSpa": ({"phone": "(850) 819-4723", "website": "panamacitylasermedspa.com"},
        "Very few reviews found online, so pitch review growth.", False),
    "Illume Medical Spa": ({"phone": "(850) 985-7848", "website": "illume-medspa.com", "email": "info@illume-medspa.com"},
        "Books online via Jane app. Only 16 Facebook reviews, so pitch review growth. Founder Nicole Johnson is the lead injector.", False),
    "Southern Serenity & Co. Med Spa": ({"phone": "(850) 814-0786", "website": "southernserenitycompany.com", "address": "2555 Huntcliff Ln, Panama City, FL 32405"},
        "Short hours: Mon-Thu 8-4, Fri 8-12, closed weekends.", False),
    "Daja View Property Management": ({"website": "dajaview.com", "address": "7009 Beach Dr, Panama City, FL 32408"},
        "5 stars (56 on Birdeye). Owners Derrek & Josh check in on guests personally every day, so it can't scale without automated guest messaging and answering.", False),
    "Emerald Coast Auto Repair": ({},
        "No website found. Open Mon-Fri 7-5:30, closed weekends. 5 stars from 26 Google reviews, BBB Torch Award.", True),
    "Affordable Auto Repair": ({},
        "No website, Facebook only. Mobile mechanic (out on jobs, so misses calls). Open 7 days 9-5. BBB A+, 40+ years experience.", True),
    "Gagnon's Tire & Auto Center": ({},
        "No website of its own found (Openbay listing only). Open Mon-Fri 7:30-5, closed weekends. Great reviews (4.8 stars, 159+).", True),
    "Ronnie's Auto Parts & Repairs": ({"website": "panamacityautorepairservice.co"},
        "3.5 stars on Yelp (23), so pitch review management. Website is an odd .co domain. Open Mon-Fri 7:30-5, closed weekends.", False),
    "Bayview Veterinary Hospital": ({"website": "bayviewveterinary.net", "address": "2333 Highway 390, Panama City, FL 32405"},
        "Profile problem: Yelp shows a duplicate 'Bay View Veterinary Hospital - CLOSED' listing at the same address, which scares off customers. AAHA accredited, since 1987.", False),
    "Bay Animal Hospital": ({"website": "bayanimalhospitalfl.com"},
        "Open Mon-Fri 8-5:30, Sat 8-3:30, closed Sun. Best of Bay 2018-2025.", False),
    "Forest Park Animal Hospital": ({"website": "forestparkanimalhospital.net"},
        "Open Mon-Fri 9-5, closed weekends. Reviews mention long wait times.", False),
    "Breeze Animal Hospital": ({"phone": "(850) 233-7091", "website": "breezevetspcb.com"},
        "Busy: 4.6 stars from 697 reviews. Closed Sunday, closes early Wednesday. Handles emergencies, so high after-hours call value.", False),
    "Studio 37": ({"website": "studio37pcb.com"},
        "Already has online booking and great reviews (4.9 stars, 167). Closed Sunday. Low-gap lead.", False),
    "Indulgence Salon": ({"website": "indulgencepcb.com", "email": "info@indulgencepcb.com"},
        "Books via Fresha. Closed Sun and Mon. 6 stylists.", False),
    "RE/MAX Freedom": ({"website": "remax-freedom-pcb.com", "address": "2908 Thomas Dr, Panama City Beach, FL 32408"},
        "RE/MAX's own site now lists this office as 'REMAX Select Partners', so it may have rebranded. Confirm the name before calling.", False),
}


def apply(path):
    rows = leadgen.load_rows(path)
    by_name = {r["business_name"]: r for r in rows}
    missing = [n for n in RESEARCH if n not in by_name]
    if missing:
        sys.exit(f"Not on the list: {missing}")
    for name, (updates, note, no_site) in RESEARCH.items():
        row = by_name[name]
        for key, value in updates.items():
            if value:
                row[key] = value
        row["research_notes"] = note
        if no_site and not row["website"]:
            row["gaps"] = NO_SITE
            row["gap_notes"] = leadgen.GAP_TEXT[NO_SITE]
    leadgen.save_rows(path, rows)
    print(f"Updated {len(RESEARCH)} businesses in {path}")


if __name__ == "__main__":
    apply(sys.argv[1])
