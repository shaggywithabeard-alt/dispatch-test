# Day AI: Company Research Brief

## 1. Snapshot

| | |
|---|---|
| **What it is** | An AI-native CRM. It has recently repositioned as **"customer memory for agents"**: one AI-ready record of every customer relationship, which people and AI agents both work from. |
| **Founded** | May 2023, Boston (registered in Winchester, MA) |
| **Founders** | **Christopher O'Donnell**, CEO. He was HubSpot's Chief Product Officer for about 10 years and led the team that built HubSpot's CRM, the main product to take on Salesforce. **Michael Pici**, co-founder. He was HubSpot's VP of Product (Revenue), came up through HubSpot sales, co-founded Stage 2 Capital, and was interim COO at Reforge. |
| **Funding** | About $24M in total. **$4M seed** (2024) led by Sequoia, with Pillar VC, Conviction, Stage 2 Capital, Inspired Capital, 20Sales and angels. **$20M Series A** (Feb 2026) led by Sequoia, with Sound Ventures, Permanent Capital, Conviction and Greenoaks. Bessemer is also named as a backer. |
| **Team** | Small, roughly 16 people per third-party data. They hire around Boston. |
| **Traction** | About 120 customers when they left private beta. General availability came with the Series A in Feb 2026. One estimate (Latka) puts revenue near $2.4M ARR, but that same source also calls them "bootstrapped," which is wrong, so I'd treat the number as unreliable. |

## 2. How the positioning has changed (important for your plan)

1. **2023–24, "AI-native CRM" / "the Cursor of CRM."** You talk to it instead of filling in fields. They pitched it as a CRM with no fixed schema: capture everything first, organise it later.
2. **Early 2026, "CRMx" plus "the Waymo of CRM."** The pitch became a self-driving CRM with the human keeping "fingers on the wheel." It replaces the CRM for startups and sits alongside the existing one for bigger companies.
3. **Mid/late 2026, "customer memory for agents," "Scale Your Company Brain," and "Claude answers questions. Agents do the work."** Their fastest-growing customers **stopped using Day AI as their CRM but kept it as the AI/context layer** on top of HubSpot, Salesforce and Gong. Day AI leaned into that. It is now mainly a memory layer plus agent platform that works alongside existing CRMs, not only a replacement.

## 3. The product today

**Customer memory (the "context graph").** Data is pulled in automatically, with permissions applied, from Gmail, Google Calendar, Day AI's own notetaker, Slack, Gong, Granola and Zapier. Billing and product-usage data are mentioned too. LLMs then decide which records to create or update. Their line is that "a database is flat; memory compounds."

**Agents as virtual employees.** Each agent has a name, a title and a job description, which works as its system prompt. Agents sit in an org chart, run **skills** on a schedule or when something happens, and deliver finished work to Slack or email: meeting prep, follow-up drafts, clean CRM records, coaching. Their stated bar is that every person should run at least two agents. The standard pair for a seller is:
- a **"CRM Data Nerd"** that keeps records accurate
- a **"Coach"** that goes deep on each deal

Other agent templates include Relationship Radar, Pipeline/Forecast Analyst, Follow-Up Drafter, Market & Account Watch, Chief of Staff and Playbook Editor.

**Instructions come in four layers:**
- a workspace-wide instruction, capped at 3,000 characters
- each agent's identity and tier
- each skill's task prompt
- the chat message or slash command itself

**Also in the product:** Pages (shared documents with PDF export), pipelines you can describe in plain language, views, CSV import, and custom properties.

**Tools for developers and outside AI:**
- A **hosted MCP server** at `day.ai/api/mcp` with OAuth sign-in. Claude, ChatGPT, Cursor and other AI tools can read and write the workspace through it.
- **[day-ai/day-ai-sdk](https://github.com/day-ai/day-ai-sdk)**, a public TypeScript SDK. It comes with Electron, Claude Agent SDK, Next.js, React Native and Vercel-cron example apps. Which tools you get depends on the tier: Free has search and meeting context; Turbo adds pages, email drafts and skills; Professional adds opportunities, pipeline analytics, imports and member management; Executive adds batch operations and `search_prospects`.
- **[day-ai/gtm-brain](https://github.com/day-ai/gtm-brain)**, a Claude Code harness last updated Aug 2026. It lets an operator plan a company's sales-and-marketing setup (they call it go-to-market, GTM), audit how well agents are being used, and deploy agents and skills into a live workspace. It also has a **pre-signup "map your GTM" mode** that produces a ready-to-apply rollout package before the customer even has an account. **This matters most for you**, because it's a ready-made playbook for partners, consultants and RevOps (revenue operations) people deploying Day AI.

**Integration gaps (from Day AI's own connector docs, verified Aug 2026):**
- **No native Microsoft 365, Outlook or Teams**. Accounts are Google-only.
- **No live two-way sync with Salesforce or HubSpot**. The bridge is a one-off CSV import plus an MCP connector for live reads.
- Setup for HubSpot, Salesforce and BigQuery requires the customer to register their own OAuth client.

**Security:** they have a SOC 2 Type II report, available under NDA at day.ai/trust. Each user sets their own privacy and sharing rules; an admin can't enforce them centrally.

## 4. Pricing (per AI agent, not per human seat)

Free, **Turbo $25**, **Professional $60**, **Executive $200** per agent per month (Ahoy's snapshot from Aug 8, 2026). Tiers allow 0, 2, 5 or 10 automated skills per agent. Annual plans are about 20% off through sales, and teammates without an agent use basic features free. Older third-party sources quote $75 and $250, so prices have moved; check the live page. The founder has said publicly that they **"don't optimize for COGS"** (the cost of the AI compute behind each customer): they're betting model costs keep falling.

## 5. Competition and risks

- **AI-native CRM startups:**
  - **Attio**: $116M raised, 5,000+ customers
  - **Lightfield**: $47M Series A in Sept 2026
  - **Clarify**: $20M+ seed, pay-per-completed-task pricing
  - smaller players: Folk, Coffee, Breakcold, Ahoy
- **The big CRMs moving into agents:** Salesforce and Anthropic announced **"Claudeforce"** on Aug 26, 2026: Salesforce inside Claude with 37 prebuilt sales skills, open beta in Sept 2026. That goes straight at Day AI's "agents run your GTM from Claude" pitch. HubSpot will do the same for its customers.
- **Criticisms in reviews** (mostly written by competitors, so discount them): you need to learn how to prompt it, tiers and skill slots are confusing, team collaboration and pipeline features have gaps, and customers have "graduated off" it as a full CRM.

## 6. What this suggests for your venture

- **The partner/consultant angle is real.** gtm-brain is built for an outside operator to discover a customer's setup, design their agents, and apply the rollout. A services or agency business that deploys Day AI agents (like a HubSpot solutions partner, but for agents) fits their model directly.
- **Build on the platform.** The SDK and MCP server let you build apps and vertical products on top of Day AI's customer memory without rebuilding the capture pipeline, which the founder says took them two years and about 2 million lines of code.
- **Openings in the gaps:** Microsoft 365 shops, two-way Salesforce/HubSpot sync, and industry-specific agent packs are things Day AI doesn't cover today.
- **Watch the platform risk.** Claudeforce and HubSpot's own agents are the main threat to any plan built only on Day AI.

**One thing to clarify:** what does your friend's "partner of day.ai" mean? It could be an investor, an employee, or a formal implementation/channel partner, and that changes a lot about how much leverage you have. Once you share the business plan and roadmap, I can map it against these capabilities and gaps.

Sources:
- [Day AI homepage](https://day.ai/), [About](https://day.ai/about), [Company](https://day.ai/company), [Pricing](https://day.ai/pricing), [MCP](https://day.ai/mcp)
- [Series A announcement](https://www.day.ai/resources/series-a-and-the-beginning-of-the-shift-in-crm), [Seed announcement](https://www.day.ai/resources/day-ai-raises-4m-from-sequoia-capital-to-reimagine-crm-for-the-ai-age)
- [Customer memory for agents](https://www.day.ai/resources/announcing-customer-memory-for-agents), [What is customer memory](https://www.day.ai/resources/what-is-customer-memory), [Gong integration post](https://www.day.ai/resources/day-ai-gong-integration)
- GitHub: [day-ai/gtm-brain](https://github.com/day-ai/gtm-brain), [day-ai/day-ai-sdk](https://github.com/day-ai/day-ai-sdk)
- Sequoia: [Partnering with Day.ai](https://sequoiacap.com/article/partnering-with-day-ai-customer-obsession-productized/), [Training Data podcast](https://sequoiacap.com/podcast/training-data-christopher-odonnell)
- Other investors: [Bessemer: Waymo of CRM](https://www.bvp.com/atlas/lessons-from-day-ais-journey-to-becoming-the-waymo-of-crm), [Pillar VC](https://www.pillar.vc/startups/day-ai-general-availability/)
- Press: [Upstarts Media](https://www.upstartsmedia.com/p/day-ai-sequoia-ai-crm), [Pulse 2.0](https://pulse2.com/day-ai-20-million-series-a/), [ContentGrip](https://www.contentgrip.com/day-ai-raises-20m-autonomous-crm/), [CO/AI](https://getcoai.com/news/day-ai-aims-to-become-the-waymo-of-crm-software/), [Agent Talk podcast](https://agenttalk.substack.com/p/infinite-markets-we-dont-optimize)
- Company data: [Tracxn](https://tracxn.com/d/companies/dayai/__jEJHyQSH2MsQWRA6SbKze4cpkwNsOva-cLSzw6f_P3g/funding-and-investors), [Latka](https://getlatka.com/companies/day.ai), [Inngest case study](https://www.inngest.com/customers/day-ai), [Releasebot](https://releasebot.io/updates/day-ai), [Ahoy pricing](https://ahoy.ai/ai-native-crm/pricing-index/day-ai/)
- Competitor reviews: [Lightfield review](https://lightfield.app/blog/day-ai-review), [Folk review](https://www.folk.app/articles/day-ai-review)
- Founder profiles: [O'Donnell (KITRUM)](https://kitrum.com/blog/the-inspiring-story-christopher-odonnell-founder-ceo-at-day-ai/), [Michael Pici (Sequoia)](https://sequoiacap.com/founder/michael-pici/)
- Competition: [Claudeforce (Salesforce)](https://www.salesforce.com/news/press-releases/2026/08/26/salesforce-and-anthropic-announce-claudeforce/), [CNBC on Claudeforce](https://www.cnbc.com/2026/08/26/salesforce-anthropic-partnership-claudeforce.html), [Lightfield Series A](https://en.wowtale.net/2026/09/12/235079/), [Breakcold alternatives](https://www.breakcold.com/blog/best-crm-alternatives-to-day-ai)

---

# Appendix: what we learned about Day AI later

## A. Can Day AI run phone, voicemail or receptionist agents?

Got it. Before you build on that, you should know: **Day AI's agents can't answer or make phone calls.** I went through Day AI's own code and docs (the SDK and the gtm-brain toolkit) and found no phone, voicemail or text-message capability. Their agents:

- **Take in** email, calendar, meeting recordings, Slack, Gong/Granola and Zapier data
- **Run** on a schedule, on one of a fixed list of 7 in-app events, or when asked
- **Deliver** to email or Slack
- **Act** through the CRM, email drafts, Pages, and connectors like HubSpot, Notion and Linear

"day-voice" in their code is a voice-chat app for talking to your own Day AI workspace, not a phone line.

So the agent building is real, but it's built for work that happens after a call, not for answering the phone. To sell an AI receptionist or voicemail product you need two layers:

| Layer | What it does | Tools |
|---|---|---|
| **1. Voice agent** | Answers the business's phone number, talks to the caller, books appointments, takes messages, texts back missed calls | Voice-agent platforms like Vapi, Retell, Synthflow (has white-label for agencies) or Bland, usually running on Twilio phone numbers |
| **2. Day AI** | Holds what the business knows about each customer, then its agents follow up on each call | Day AI's SDK or its MCP server (the connection AI tools use to read and write your Day AI data) |

How the two connect:
1. The voice platform finishes a call and sends the transcript and caller details to a small connector program.
2. The connector writes them into Day AI: it creates or updates the contact and logs the call.
3. Day AI agents do the rest:
   - send the owner a morning summary of yesterday's calls
   - draft follow-up emails
   - flag unhappy customers
   - keep the pipeline up to date

**The pitch:** the phone gets answered, and every caller is remembered and followed up on. Most AI-receptionist agencies only offer the first half; Day AI gives you the second.

**Three things to confirm with your friend:**
1. **Each client probably needs their own Day AI workspace.** Pricing is per agent (roughly $25–$200 a month each), so ask whether partners get an agency or multi-client setup and partner pricing.
2. **Accounts are Google-only.** Clients on Outlook or Microsoft 365 can't connect their email natively.
3. **Can Day AI's events be triggered by an outside system** like a phone platform? The public docs show a closed list of 7 in-app events. If not, the connector can create the record and a scheduled agent picks it up every few hours.

I can build that connector next: a small service that takes a finished call from the voice platform and writes it into Day AI through their SDK. Pick the voice platform first; Vapi or Retell are the usual choices for building a custom product. Then have your friend check point 3.

Sources: [Retell AI](https://www.retellai.com/blog/best-ai-voice-agents-automated-phone-calls), [Synthflow](https://synthflow.ai/), [Bland](https://www.bland.ai/), [Day AI SDK](https://github.com/day-ai/day-ai-sdk), [Day AI gtm-brain](https://github.com/day-ai/gtm-brain)

## B. Day AI vs. Google Workspace for sending cold email

No. Google Workspace doesn't charge per email, and Day AI can't send the cold emails for you anyway.

**Google Workspace pricing is flat.** Business Starter is about **$7 per user per month on an annual plan, or $8.40 month-to-month**. Unlimited sending up to Google's daily cap, which is far above the 20–30 a day a new domain should send. One user is enough to start.

**Day AI is the wrong tool for this step.** I checked its developer docs:
- **It only drafts email.** Its email tool creates a *draft*, and the "from" address must belong to *your connected account*. You still click send, or something else sends it.
- **It connects to Gmail, which means Google.** Day AI's email connection is Gmail-only, so you'd need a Google account either way.
- **Its "send" tool only reaches you.** It sends notifications to you or your team by email or Slack. It has no option for emailing an outside business.
- **It costs more.** Pricing is per agent, about **$25–$200 per agent per month**, on top of the Google account.

| | Google Workspace | Day AI |
|---|---|---|
| Cost | ~$7–8.40/month flat | ~$25–200/agent/month, plus a Google account |
| Sends cold emails | Yes | No (drafts only) |
| Per-email charges | None | None |

**Where Day AI does pay off is after people reply.** It can remember every prospect's calls and emails, draft personal follow-ups, and remind you who to call back. Bring it in once replies and clients start coming in.

**My recommendation:** get **one Google Workspace user on your new domain** for about $7–8.40/month, then connect it to the Gmail connector here. I'll send the first-touch emails through it, logged in the spreadsheet, at 20–30 a day while the domain warms up. Once you have it, send me the sending address, the name and company name for the emails, a mailing address, and your callback number.

## C. Questions for Austin Gentile (Day AI partner)

Here are the questions I'd bring, grouped and in priority order. Each one targets a gap we hit while building this.

### 1. Pin down what "partner" means (ask first)
1. **What exactly is your role with Day AI:** investor, employee, or an official partner/reseller? Is there a formal partner program we can join?
2. **Can we use the Day AI name in our pitch** ("a Day AI partner")? Anything in writing that allows it?
3. **How do partners make money:** referral fees, a share of revenue, reselling at a markup, or charging only for our own setup and services?
4. **Who owns the client relationship and the billing,** us or Day AI?

### 2. Pricing for our clients
5. **Is there partner pricing or a discount** off the $25–$200 per-agent price?
6. **Does every client need its own workspace,** or is there an agency account where we manage many clients from one login?
7. **Is a free or cheap pilot possible** so a client can try it before committing?
8. **Can we run our own agency on Day AI** for free or at a discount, to track our leads and clients?

### 3. Can it do what we're selling?
9. **Phone and texting:** Day AI has no phone, voicemail or text features today. Is anything on the roadmap? If not, which voice platforms do they recommend pairing with?
10. **Can an outside system trigger an agent?** The public docs show a fixed list of 7 in-app events. If a call-answering service finishes a call, can that kick off a Day AI follow-up right away?
11. **Microsoft/Outlook support:** Day AI is Google-only. Many local businesses use Outlook, so when does Microsoft 365 arrive?
12. **Sending outreach email:** their email tool only creates drafts. Confirm Day AI can't send emails to outside businesses, so we plan around it.
13. **Is it a fit for local businesses** (dentists, plumbers, salons, auto shops), or is it really built for startup sales teams? Ask for any small-business customer examples.

### 4. Compliance (important for your list)
14. **HIPAA:** will Day AI sign a Business Associate Agreement (BAA)? Your list includes dentists, chiropractors and med spas. Recording patient calls or storing patient emails without a BAA is a legal problem for them and for you.
15. **Can we get the SOC 2 report** (under NDA) to show clients who ask about security?

### 5. Support and getting started
16. **Can we get a demo workspace** to show prospects live?
17. **Training and onboarding:** is there partner training? Who do we call when something breaks for a client, and how fast do they respond?
18. **Will Day AI send us leads,** such as small businesses asking for setup help, or do co-marketing with us?

### 6. Between you and Austin (get this in writing)
19. **What's he contributing:** time, money, Day AI access, or introductions? What's his expected share?
20. **Who does what:** sales, building the agents, client support?

If you only have five minutes, ask **#1, #3, #5, #9 and #14**. Those decide whether the business model works.
