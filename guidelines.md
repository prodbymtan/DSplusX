# Relay: Full Team Context

Oct 24, 2026 · @Keene

## How to use this doc

This is the single source of truth for Relay, our DS+X Hackathon 2026 project (Health + Biotech track). It holds every decision, rule, data source, and open question from our planning so far. Give it to your AI assistant (Kiro, Claude, or anything else) before asking it to build anything, so it doesn't contradict what the team already decided.

Short version: see *Relay: Project Overview*.

**Rule for every AI prompt:** everything we build must follow the laws and guidelines in the "Laws, ethics, and guidelines" section below. If an AI suggests something that conflicts, the doc wins.

**Team:** 5 people, all fairly new to hackathons. We are submitting to DS+X only (not Hackachusetts, which caps teams at 4).

## Event basics

DS+X Hackathon 2026 runs Saturday Oct 24 to Sunday Oct 25 at BU's Center for Computing & Data Sciences, 665 Commonwealth Ave. Our hard deadline is Sunday 11:00 AM on Devpost.

### Deadlines and must-dos

| When | What | Notes |
|---|---|---|
| Sat 8:15 PM | Evening session | Mandatory for everyone. Covers how to submit |
| Sat 9:30 PM | Devpost project page created | Create it, keep editing until the deadline |
| Sat, on Devpost | List every teammate | Anyone not listed can't win a prize; every member needs a Devpost account |
| Sun 11:00 AM | Final submission | Hard deadline. "Saved" is not "Submitted": verify the status |
| Sun 11:30 AM to 1:00 PM | Project presentations | 3 minutes per team, no Q&A |
| Sun ~2:45 PM | Closing ceremony and awards | |

### Saturday schedule (from opening session)

- Opening ceremony, then team formation and track rooms
- Workshops round 1 (11:15 AM to 12:15 PM): Figma with AI (264), Building with Kiro (B62), Team speed dating (262)
- Lunch and group photo
- Workshops round 2 (1:15 to 2:15 PM): Intro to Lovable (264), Intro to Computer Vision (262), RAGs, MCPs & AI Agents (262), Building with Kiro (B62)
- 2:00 PM: Ethics Genius Bar opens; then open build time
- 6:30 PM: dinner
- 10:00 PM: sleeping rooms open (262 and 263); late-night snacks and karaoke around midnight
- Sunday 8:00 AM: breakfast

### Rules

- Team size for DS+X: 3 to 5 people. Hackachusetts allows max 4, so our team of 5 is DS+X only.
- Build during the event. Don't bring in old projects or old code.
- All AI tools are allowed (Kiro, Lovable, Figma, Claude, etc.).
- Stay on the basement, 1st, and 2nd floors. Not the 3rd floor or above.
- Wear your wristband. Building entry/exit times were announced at the opening; confirm the exact rules with an organizer (non-BU students can't re-enter between about 7 PM and 8 AM).

### Support

- **Mentors:** mentor stations for every track (slide said from 3:00 PM in the Mentor Space; organizers also said mentors are around until 8 PM and again Sunday morning)
- **Ethics Genius Bar:** 2:00 to 6:00 PM, lower level (yellow space). Privacy, fairness, impact. Ethics is part of judging.
- **Librarians' Corner:** BU librarians help find data, research, and sources. Also tied to a BU Libraries prize.
- **Discord:** BU Spark! server for announcements, room changes, and mentors. Resource guide and slides get posted there.

### Prizes

Devpost lists $7,500 in total prizes. From the opening: one top overall prize (about $1,000), 1st and 2nd for Health + Biotech, 1st/2nd/3rd for CollegeHack, 1st/2nd for ArtHack, two Best First-Time Hacker prizes, plus a BU Libraries prize and sponsor prizes (e.g. best use of specific tools).

## Judging

Half the score is idea and problem fit; 40% is whether it works and is easy to use; ethics is 10% on its own. Presentation is only 5%, but it's 3 minutes with no Q&A, so anything unsaid must be on Devpost.

### DS+X rubric (from the Devpost Rules tab)

| Weight | Criterion | What judges look for | How Relay wins it |
|---|---|---|---|
| 25% | Idea & Relevance | Creativity and potential impact | Connects four gaps for one patient; hits H1 and H2 |
| 25% | Technical Execution | Functionality, stability, usability, innovative use of tools; working demos over unrealistic deployment | Stable demo with cached data, real-time notification, no crashes |
| 20% | Problem-Need Fit | Clear problem and alignment with user needs | Maria persona, cited wait-time and MassHealth stats, mentor quotes |
| 15% | Design | UX clarity, navigation, consistency, accessibility, thoughtful details | Simple flows, large text, screen-reader labels, plain language |
| 10% | Responsibility & Ethics | Privacy, bias, fairness, accessibility, transparency | Data on device, auto-delete, no diagnosis, fair queue, nearest ER always |
| 5% | Presentation | Clarity, engagement, communicating purpose and impact | Two-phone live demo |

Devpost also asks two ethics questions every team should answer on its page:

1. What ethical and responsibility concerns are relevant to your project?
2. How has your team addressed these issues, or what steps do you still need to take before deployment?

### The six pillars (opening slide)

1. **Problem understanding:** do you understand the problem and who it affects?
2. **Relevance and impact:** does it address the challenge and make a difference?
3. **Technical execution:** does it work, and is it built well?
4. **Ethics:** is it responsible, fair, and safe?
5. **Design:** is it clear, usable, and thoughtfully put together?
6. **Presentation:** can you explain it clearly in your demo?

### Ethics rubric: five principles (opening slide)

| Principle | Meaning | Relay's answer |
|---|---|---|
| Data Privacy & Security | Keep user data protected | Health data stays on the device; delete anytime; 90-day raw data retention |
| Fairness | Mitigate bias, treat all users equitably | Longest-wait-first queue, not fastest-tap-wins |
| Transparency | Clear models, reasoning, and disclosures | No AI in the summary; every number traces to raw data; simulated data labeled |
| Human Centered | Prioritize real human needs and well-being | Never diagnoses or decides eligibility; doctor and MassHealth decide |
| Inclusion & Accessibility | Accessible across diverse abilities | Works on any device; no-wearable mode; printable PDF and card; WCAG 2.1 AA |

## Track and challenges

We're in Health + Biotech and target H1 and H2. The track shares its challenge list with the statewide Hackachusetts campus data portal; the portal calls them "guidance only, not the final brief," so we can shape our own solution.

| # | Challenge | Challenge statement | Ours? |
|---|---|---|---|
| H1 | Turning wearable data into better healthcare | "Continuous monitoring is not yet better care." | Yes, core |
| H2 | Keeping residents connected to health coverage | "Renewal notices miss people." | Yes |
| H3 | Improving healthcare access and coordination | "A referral is not a finished visit." | Touches it (waitlist) |
| H4 | Accelerating biotechnology innovation | "Discovery is slow, expensive, and hard to translate." | No |
| H5 | Making clinical research more accessible | "Finding a trial is harder than joining one." | No |

### Portal guidance worth following (it reflects what judges value)

- Plain language; cite the agency for every dataset.
- "The state decides eligibility. Clinical decisions stay with qualified professionals." Our app explains and routes, never decides.
- Label synthetic or simulated data on every screen.
- WHOOP and similar device data needs the member's consent; the WHOOP API is OAuth, not a bulk download.
- Use standards instead of inventing formats: HL7 FHIR for records and scheduling, the CMS Care Update Template for handoffs.

### Portal datasets relevant to us

| Dataset | Tagged for | What it is | Our use |
|---|---|---|---|
| PhysioNet wearable device dataset | H1 | Wearable signals: heart rate, stress, movement, temperature | Vitals (primary) |
| CDC PLACES short sleep | H1 | Share of adults sleeping under 7 hours by MA county, 2022 | Optional context |
| Synthea patient table (column guide) | H1, H2, H3 | Synthetic patient schema, no real people | Optional for fake waitlist patients |
| CMS Care Update Template | Handoffs | Fields one care team tells the next | Shape of the Doctor view |
| HL7 FHIR | Records | Health data exchange standard | Future clinic integration (Slot, Appointment) |
| MassHealth federal updates, CMS Medicaid eligibility | H2 | Policy pages, not APIs | Link from coverage feature |
| CDC PLACES MA, Census insurance, CDC SVI, CHIA | H2, H3 | Burden and coverage context | Optional stats for pitch |
| MassGIS acute hospitals, CMS hospital ratings (Emergency Yes/No) | H3 | Hospital locations and ER flag | Emergency mode |
| HRSA Data Warehouse | H3 | Shortage areas and health center data | Clinic list |
| MassGIS environmental justice block groups | H2, H3, H5 | Income, race, language flags by block group | Optional: where outreach matters most |

## The product: Relay

Relay is a web app that carries a patient's health information and access to care from one step to the next, solving H1 (wearable data into better care) and H2 (staying connected to coverage) at once. It turns wearable data into a plain snapshot a doctor or ER can read in under a minute, helps patients get seen sooner through a fair waitlist at community health centers, points to the nearest ER in an emergency with no insurance check, and tracks MassHealth renewal dates so coverage doesn't quietly lapse. **Relay never diagnoses and never decides eligibility: it displays, reminds, explains, and routes.**

**Why the name:** Relay passes information along: your data to the doctor, open slots to you, and your renewal reminder before it's too late.

### One app, two views

- **Patient view:** vitals and Doctor view, waitlist, emergency mode and card, coverage countdown.
- **Clinic view:** front-desk staff post openings and see their waitlist. No health data.

### Four features, in build order

1. Vitals + Doctor view + PDF (H1)
2. Waitlist + clinic view + instant notification (access, bridges H1 and H2)
3. Emergency mode + emergency card (H1)
4. Coverage countdown (H2)

If 3 or 4 aren't solid by Sunday morning, cut them from the live demo and describe them on Devpost as next steps.

### Demo persona (fictional)

**Maria Santos**, 34, home health aide in Dorchester, MassHealth member. She wears a basic fitness band. Lately her heart races at work even when she's sitting still. Her community health center's next opening is 9 weeks out, and her MassHealth renewal is due in 3 weeks under the new 6-month rules. Label her "Fictional demo persona" on every screen. She shows all four features: her data (H1), her waitlist spot (access), her emergency card (H1), her renewal countdown (H2).

## Decision log

These are locked unless the whole team agrees to change one.

| # | Decision | Why |
|---|---|---|
| 1 | Submit to DS+X only; deadline Sun 11 AM | Team of 5 exceeds Hackachusetts' max of 4 |
| 2 | Name: Relay | Fits all four features |
| 3 | Target H1 + H2 | Two problems in one product |
| 4 | Web app, built in React, mostly with Kiro | Accessibility, works on any device |
| 5 | No AI in the doctor summary; rules and templates only | No diagnosis risk, no API key, full transparency |
| 6 | Vitals come from PhysioNet data (not live Garmin/WHOOP) | Real data, no consent or OAuth setup needed |
| 7 | Sync on demand ("Sync device" button), not constant live sync | Simpler and more private |
| 8 | MassHealth only for insurance | One plan to model; perfect for H2 |
| 9 | Clinics = real community health centers (HRSA list) with simulated slots | Health centers must serve everyone regardless of ability to pay; no public slot data exists |
| 10 | One app, two views: patient + clinic | Clinic view powers openings and the demo moment |
| 11 | Health data stays on the patient's device; only slots and waitlist live on the server | Privacy; keeps us out of HIPAA business-associate territory for health data |
| 12 | Queue: longest wait first, 5-minute claim window; no-shows go to the top 3 at once | Fair and still fast |
| 13 | Doctor sharing = Doctor view on the patient's phone + PDF download; email optional with a security warning | Email isn't secure for health data |
| 14 | Emergency mode = nearest ER always, no insurance filter | EMTALA and No Surprises Act protect patients |
| 15 | Emergency card = static lock-screen image + guided Medical ID setup; live pre-accident data is a future feature | A web app can't bypass the lock screen |
| 16 | Retention: raw data 90 days, summaries 1 year, "Delete everything" button | Data minimization |
| 17 | No wearable? Wearable features turn off; everything else works | Inclusion |
| 18 | Describe, never interpret in any health text | FDA wellness rules; doctors interpret |
| 19 | In-app notifications only, no SMS | Text-message law (TCPA) |
| 20 | Never collect SSNs, MassHealth ID numbers, or financial info | Massachusetts data security rules |
| 21 | Demo persona Maria Santos (fictional) | Shows every feature in one story |
| 22 | Every Kiro task is small and focused, each member using their 2,000 credits on separate pieces | Higher-quality code |

## Feature specs

### 1. Vitals + Doctor view + PDF (H1)

- **Sync:** a "Sync device" button loads the preprocessed PhysioNet data into the browser. Show "Last synced: [time]".
- Per-minute averages of: heart rate, HRV (from IBI), skin temperature (labeled "skin temp, not body temp"), activity level (from ACC). EDA (sweat response) only in a detail view.
- **Never shown:** blood oxygen, blood pressure, sleep (the device doesn't measure them).
- Timeline charts over the recording, plus simple stats: average, resting, max, and when spikes happened, always paired with movement context ("HR 125 bpm at 2:10 PM while movement was low").
- **Doctor view:** one tap, full-screen, readable in under 60 seconds. Patient name, sync date, the key stats, the charts, and user-entered conditions, meds, and allergies. Field layout inspired by the CMS Care Update Template.
- **PDF export:** same content, for the patient to send through their patient portal.
- **Email (optional):** only if the patient chooses it, with a warning that email isn't secure.
- **Footer on every summary:** "Data from a consumer wearable. Not a medical device. Not a diagnosis."
- **Wording rule: describe, never interpret.**
  - Allowed: "Heart rate was above 120 bpm for 14 minutes while movement was low."
  - Not allowed: "possible panic attack," "irregular heartbeat," "abnormal," red warning flags, or any threshold that tells the user to seek treatment.

### 2. Waitlist + clinic view + instant notification

- **Patient side:** pick a clinic (community health centers from the HRSA list), see the next regular opening, tap "Join waitlist," set preferred days and times.
- **Clinic side:** a front-desk page with "Post opening" (date, time, length, visit type) and "Mark no-show." It shows the clinic's waitlist: first name, how long they've waited, preferred times. No health data.
- **Queue rule:**
  - A slot opens; the patient who has waited longest (and matches the time) is notified instantly.
  - They get 5 minutes to claim it. A countdown shows on their screen.
  - No claim → it moves to the next person in line.
  - No-show or under ~1 hour away: notify the top 3 longest-waiting matches at once; first to claim gets it.
  - Claimed → both views update instantly; the patient's old appointment is released back to the queue.
- Show the rule on screen ("You're #2 in line. Longest wait goes first."). Notifications are in-app only, opt-in. Appointment slots are labeled "Simulated".

### 3. Emergency mode + emergency card (H1)

- **Emergency mode:** a big button. Shows the nearest ER (hospitals with emergency services from MassGIS/CMS data), distance, a Call 911 button, and a line: "ERs must treat you regardless of insurance. You won't be denied emergency care." No insurance filter.
- **Emergency card:** a form (all optional): conditions, allergies, medications, blood type, emergency contact, plus wearable baselines ("usual resting HR: 62 bpm, updated Oct 24").
- **"Make lock screen card":** generates a downloadable image the user sets as their wallpaper; the user picks what appears on it.
- Guided setup for iPhone Medical ID and Android Emergency Info, which first responders can open without a passcode.
- **Future only (Devpost):** opt-in, logged, expiring emergency access to recent vitals ("break-glass access").

### 4. Coverage countdown (H2)

- User enters (or picks in the demo) their next MassHealth renewal date.
- Shows a countdown, a plain-language "what to expect" explainer, and reminders at about 30, 14, and 7 days.
- Explains that some members will need to renew every 6 months starting in 2027, and links the official MassHealth page.
- Never says whether someone qualifies. "MassHealth decides eligibility. This is a reminder, not a decision."
- Never asks for a MassHealth ID number.

### Across the whole app

- **Settings:** Delete everything, Disconnect device, retention settings (raw data 90 days, summaries 1 year by default).
- **Accessibility:** WCAG 2.1 AA contrast, screen-reader labels, large-text option, keyboard navigation. Spanish if time allows.
- **No wearable:** wearable features hide; waitlist, emergency, and coverage still work.
- **No smartphone:** works on any browser (library or clinic computers); PDF and emergency card can be printed.

## Data

Vitals, clinics, and hospitals are real public data; appointment slots and Maria are simulated or fictional and labeled that way. No public dataset of open appointment slots exists, because schedules live inside each clinic's private system.

| Data | Source | Real or simulated | Used for |
|---|---|---|---|
| Wearable vitals | PhysioNet Wearable Device Dataset v1.0.1 (open access) | Real, de-identified | Vitals, Doctor view, baselines |
| Community health centers | HRSA Data Warehouse, health center sites (filter to MA) | Real names and locations | Waitlist clinics |
| Hospitals with ERs | MassGIS acute hospitals + CMS hospital ratings ("Emergency" column) | Real | Emergency mode |
| Appointment openings and waitlist patients | Built by us (optionally Synthea-style names) | Simulated | Waitlist demo |
| Maria Santos | Built by us | Fictional | Demo persona |
| MassHealth renewal rules | Mass.gov | Real, linked not copied | Coverage countdown |

### PhysioNet dataset details

- Recorded with an Empatica E4 research wristband during structured lab sessions: 36 volunteers in STRESS sessions, 30 in AEROBIC cycling, 31 in ANAEROBIC cycling. Includes self-reported stress scores and age, weight, height.
- Three folders (STRESS, AEROBIC, ANAEROBIC), one subfolder per participant, with files: `HR.csv` (heart rate), `IBI.csv` (time between beats), `TEMP.csv` (skin temp), `EDA.csv` (sweat response), `ACC.csv` (3-axis movement), `BVP.csv` (raw pulse wave), plus tags for segmentation.
- Typical E4 CSV layout (verify when you open the files): row 1 = start time as a Unix timestamp, row 2 = sample rate in Hz, then the readings. Roughly HR 1 Hz, TEMP and EDA 4 Hz, ACC 32 Hz, BVP 64 Hz; IBI is irregular (one row per beat).
- Some sessions are incomplete or have artifacts; the dataset documents these.
- Cite PhysioNet's standard citation on Devpost.

### Preprocessing plan (Python, done once)

1. Load each file for the chosen participant(s).
2. Convert timestamps; resample to 1-minute windows.
3. Per window: mean HR, HRV (RMSSD from IBI), mean skin temp, mean EDA, movement magnitude from ACC.
4. Pick one participant and stitch their stress and exercise sessions into Maria's "recent day." Say so on Devpost.
5. Export to a small JSON file the React app loads on "Sync device."

### What the device doesn't measure

No blood oxygen, no blood pressure, no sleep staging. Don't show or imply them.

## Tech stack

React web app on Vercel, Supabase for slots and real-time notifications, and the browser itself for health data. No AI API key is needed because the summary is built from rules, not AI.

| Layer | Choice | Holds | Why |
|---|---|---|---|
| Frontend | React (Vite) + Tailwind CSS | All screens, both views | Team's choice; Kiro builds it well |
| Charts | A React chart library (e.g. Recharts) | Vitals timelines | Fast, accessible charts |
| Health data storage | Browser storage (IndexedDB) on the patient's device | Vitals, emergency card info, renewal date | Privacy: never touches our server |
| Server data | Supabase (Postgres) | Clinics, slots, waitlist entries (first name, wait time, preferences) | Team already knows it |
| Real-time | Supabase Realtime | Instant slot notifications | Clinic posts, patient sees it within a second |
| PDF | Client-side PDF library | Doctor summary export | Generated on the device |
| Data prep | One Python script (pandas) | PhysioNet → per-minute JSON | Run once, ship the JSON |
| Hosting | Vercel (free) | The live demo link | One-click deploys from GitHub |
| Code | GitHub repo | Everything | Every teammate commits |

**Kiro:** optional for DS+X (it was only required for Hackachusetts), but each teammate has 2,000 credits and the team chose it. Use Specs (requirements → design → tasks) and a steering file in `.kiro/steering/` with these project rules. Commit the `.kiro` folder.

**Secrets:** Supabase keys go in environment variables, never in GitHub. Add `.env` to `.gitignore` before the first commit.

### Architecture

*(Architecture diagram embedded in the original doc.)*

Only appointment data (clinics, slots, waitlist) crosses to the server; vitals and the emergency card reach a doctor only when the patient shows or exports them.

## Laws, ethics, and guidelines

Every feature must stay inside these rules. This is research, not legal advice; the team will review it at the Ethics Genius Bar. A hackathon prototype isn't a marketed product, but we design as if launching.

| Area | Rule | What it says | How Relay complies |
|---|---|---|---|
| Vitals display | FDA General Wellness guidance (Jan 6, 2026) | Wellness products may display values, ranges, trends, baselines, and longitudinal summaries but must avoid clinical claims, thresholds, or prompts for medical management | Data and trends only; no "abnormal" labels, flags, or treatment prompts; "Not a diagnosis" footer |
| Health data on the patient side | FTC Health Breach Notification Rule (2024 update) | Applies to health apps not covered by HIPAA; breaches must be reported | Data stays on device; never sold or shared; breach plan described on Devpost |
| Clinic view | HIPAA | A launched service holding waitlists for clinics becomes a business associate (needs an agreement and safeguards) | Demo uses fake patients only; clinic sees minimum info; no health data |
| Emergency mode | EMTALA + No Surprises Act | ERs must screen and stabilize anyone regardless of insurance; emergency out-of-network billing is limited | Nearest ER always; no insurance filter; protections explained on screen |
| Clinic list | HRSA Section 330 | Health centers must serve all individuals regardless of ability to pay | Real centers, simulated slots, labeled |
| Coverage | MassHealth's authority | Only MassHealth decides eligibility | Remind, explain, link; never decide; no ID numbers collected |
| Notifications | TCPA | Texting people requires specific consent | In-app notifications only, opt-in |
| Personal info | Massachusetts data security rules | Strict rules for SSNs, license, and financial account numbers | We never collect them |
| Accessibility | WCAG 2.1 AA | Standard for accessible web apps | Contrast, labels, large text, keyboard use |
| Data sources | Each dataset's terms | PhysioNet, HRSA, CMS, MassGIS are public; cite them | Cite every source; label synthetic data |

### Ethics design rules (for every AI prompt)

1. **Describe, never interpret.** No diagnoses, no risk scores, no "you should see a doctor because…" prompts.
2. **The patient controls sharing.** Nothing leaves the device unless they tap Share, Download, or Email.
3. **Minimum data.** Only collect what a feature needs.
4. **Label everything simulated or fictional on screen.**
5. **Fair queue:** longest wait first, and explain the rule on screen.
6. **Known equity gap:** people without smartphones or wearables. Answer: works in any browser, no-wearable mode, printable PDF and card.
7. **Known limitation:** PhysioNet is lab data from healthy volunteers, not real patients' daily life.

## Competitors and originality

Each feature exists somewhere on its own; no product we found combines all four, and our waitlist uses a fairer rule. **Never claim "nothing like this exists."** Say: "These tools exist in pieces. Relay connects them for the patients most likely to fall through the gaps."

| Our feature | Closest existing | How Relay differs |
|---|---|---|
| Waitlist + notify | Epic MyChart Fast Pass: offers go to several patients at once, so quick action is key; some clinics only check for openings each evening. Zocdoc shows open slots filtered by insurance | Longest wait first; doesn't require Epic; built for community health centers |
| Wearable data for doctors | Apple Health sharing; wearable apps' exports | Doctor-ready one-page snapshot; device-agnostic; patient-controlled |
| Emergency card | iPhone Medical ID, Android Emergency Info | Guided setup plus wearable baselines |
| Coverage reminders | MassHealth's own letters and outreach | Lives in the app the patient already uses for care |

- The research doc a teammate pasted claimed no app does real-time cancellation booking. That's wrong (see MyChart Fast Pass); don't repeat it. Its "rideshare-style geofenced standby" ideas are interesting but out of scope and raise location-privacy issues.
- **Name:** Relay is used by other health tech companies (e.g. RelayHealth, Relay Network). The team decided that's fine for the hackathon since our product is different.

## Pitch and demo plan (draft)

3 minutes, no Q&A, so the demo carries it. The centerpiece is two phones side by side: the clinic posts an opening and Maria's phone buzzes instantly. We'll refine this after the product works.

| Segment | Time | Content |
|---|---|---|
| Hook | 15 sec | Maria's story, plus a verified wait-time stat |
| Waitlist | 45 sec | Clinic phone posts a cancelled slot; Maria is first in line because she's waited longest; she claims it |
| Doctor view | 45 sec | At the visit, she taps Doctor view; the doctor sees her heart-rate spikes with movement context |
| Coverage | 20 sec | "Renewal in 21 days," with the official MassHealth link |
| Emergency | 15 sec | Nearest ER, no insurance check; the lock-screen card |
| Ethics | 25 sec | Data stays on the phone, auto-deletes, never diagnoses, fair queue |
| Close | 15 sec | The H1 + H2 line and what's next |

Rehearse with a timer. Have a backup screen recording in case wifi fails.

## Devpost plan

Devpost is the full version of the pitch; judges read it during deliberations, so everything we can't say in 3 minutes goes here.

- [ ] Project page created by Sat 9:30 PM, all 5 teammates listed
- [ ] **Inspiration / problem:** Maria's story, H1 and H2, cited stats
- [ ] **What it does:** the four features with screenshots
- [ ] **How we built it:** React, Supabase, PhysioNet preprocessing, how we used Kiro
- [ ] **Data sources:** every dataset cited (PhysioNet citation, HRSA, CMS, MassGIS, Mass.gov)
- [ ] **Real vs. simulated:** clear table
- [ ] **Ethics:** answer Devpost's two questions, organized by the five ethics principles; include the laws table
- [ ] **Limitations:** lab data, simulated slots, no live device sync yet
- [ ] **What's next:** Garmin/WHOOP OAuth sync, FHIR scheduling integration, break-glass emergency access, Spanish
- [ ] Demo video link (optional but helpful)
- [ ] Status shows **Submitted** before Sun 11:00 AM

## Team workflow and roles

Plan: agree on the architecture first, then each person builds small, separate pieces in Kiro so the AI output stays high quality. Roles below are a starting suggestion; we'll finalize them when we start building.

| Person | Suggested area |
|---|---|
| 1 | App shell, routing, shared components, patient view screens |
| 2 | PhysioNet preprocessing script → JSON; vitals charts |
| 3 | Supabase tables, clinic view, queue logic, real-time notifications |
| 4 | Emergency mode (hospital data), emergency card, coverage countdown, clinic list (HRSA) |
| 5 | Design and accessibility, ethics write-up, Devpost page, pitch |

### Kiro rules for everyone

- Paste this doc's key sections (Decision log, Feature specs, Laws and ethics) into a shared steering file in `.kiro/steering/` so every Kiro session follows the same rules.
- One feature or component per Spec. Small tasks beat giant prompts.
- Read every diff before accepting. You need to be able to explain your code.
- Pull before you start, commit and push after each working piece.
- If Kiro suggests something that breaks a decision or a rule in this doc, the doc wins.

## Ideas considered and rejected

Listed so no one (or their AI) re-proposes them without knowing why they were dropped.

| Idea | What it was | Why we dropped it |
|---|---|---|
| TrialMatch | Plain-English clinical trial search | NIH already built TrialGPT; obvious H5 pick |
| Bottleneck | Estimate how many people qualify for a trial using NHANES | Original but abstract; no personal hook |
| Beyond BMI | Show where BMI mislabels people | Research already exists; body-image risk |
| Supplement scanner | Check supplement labels for banned substances | Crowded (NSF, Informed Sport, NutriSee, Drug+) |
| Crunch Forecast | Predict stressful weeks from syllabi + sleep | Too complicated and too personal |
| Pulse | Anonymous campus stress check-ins | Didn't fit the track's challenges |
| Brief | Classify stress vs. exercise from wearable data | Not seen as a winner; parts live on in Relay's vitals feature |
| Insurance-filtered ER finder | Nearest in-network ER | Unsafe and unnecessary: ERs must treat everyone (EMTALA); routing by network could delay care |
| Email-first doctor sharing | Email the summary to the doctor | Email isn't secure for health data; now optional with a warning |
| Live pre-accident data on lock screen | Show recent vitals without unlocking | Web apps can't; serious privacy risk; future opt-in feature only |

## Stats to verify before using

These came from AI-generated research a teammate pasted, not from sources we opened. Find the original source for each before it goes on a slide or Devpost.

| Claim | Claimed source | Status |
|---|---|---|
| Average new-patient wait in the US is 31 days | AMN Healthcare survey | Verify |
| Boston has the longest waits (about 65 days) vs. Atlanta (12 days) | AMN Healthcare survey | Verify; great pitch hook if true |
| Medicaid acceptance 53% vs. Medicare 82% among physicians | Unclear | Verify |
| High-performing automated waitlists fill about 38.8% of something (exact measure unclear) | NIH-published paper on automated waitlists | Verify what the 38.8% measures before citing |
| Only 11% of medical groups report high patient use of digital self-scheduling | Unclear | Verify |
| Physician shortage up to 86,000 by 2036 | Unclear (often AAMC) | Verify |

**Already verified (sourced):** about 2 million MassHealth members; about 360,000 may face new work and education requirements starting January 2027, many with 6-month renewals (Mass.gov). Keep the pitch neutral: describe the rule change, don't editorialize.

## Open to-dos and questions

- [ ] Every teammate: Devpost account, joined the team's project
- [ ] Finalize roles and write the shared Kiro steering file
- [ ] Create the GitHub repo; add `.env` to `.gitignore` first
- [ ] Download the PhysioNet dataset and pick Maria's participant
- [ ] Download HRSA health center sites; filter to Massachusetts (Boston-area centers for the demo)
- [ ] Pull the hospital list with ER flags (MassGIS / CMS)
- [ ] Take the laws table to the Ethics Genius Bar (2 to 6 PM); note what the mentor says for Devpost
- [ ] Ask the Librarians' Corner to confirm health centers' MassHealth acceptance and help verify the stats
- [ ] Talk to 1 or 2 mentors about the problem; get quotes for Problem-Need Fit
- [ ] Create the Devpost page by 9:30 PM
- [ ] Attend the mandatory 8:15 PM session
- [ ] Decide: email sharing in or out of the demo?
- [ ] Decide: Spanish language support if time allows?
- [ ] Rehearse the 3-minute pitch Sunday morning; record a backup demo video
- [ ] Confirm Devpost status shows Submitted before 11:00 AM Sunday

## Sources

- Relay: Project Overview (our short doc)
- PhysioNet Wearable Device Dataset
- Mass.gov: Federal changes affecting MassHealth members
- Mass.gov: Statewide campaign to help MassHealth members keep coverage
- MassHealth advisory meeting, Jan 2026 (about 2M members)
- FDA wellness guidance summary (Arnall Golden Gregory)
- FDA wellness guidance summary (ArentFox Schiff)
- FTC: Updated Health Breach Notification Rule
- CRS: Federal Health Centers overview
- MyChart Fast Pass (Austin Regional Clinic)
- MyChart Fast Pass (Good Samaritan)
- DS+X Devpost Rules tab and the opening-session slides (judging, ethics rubric, deadlines)
- Hackachusetts campus data portal (challenge list and datasets for the shared Health track)
