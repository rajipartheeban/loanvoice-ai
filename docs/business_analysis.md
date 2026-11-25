# Business analysis

## 1. Problem statement
Indian digital lending apps (KreditBee, Moneyview, Fibe, CASHe) have high average ratings (4.5-4.8, except
CASHe at 3.1), but this hides a concentrated set of problems. Of 121,688 Google Play reviews (May-Nov 2026),
only 5,874 name a specific problem - yet they cause over half of all 8,979 one-star reviews.

Who is affected: borrowers - most of all existing customers who repaid on time and are then refused a new
loan (~730 say so), and borrowers whose payments are not recorded or who are penalised anyway.
What goes wrong: (1) loans refused with no reason, even to good repayers; (2) aggressive recovery calls;
(3) repayment problems - payments not updated, penalties despite paying, app down on EMI day.
What it costs: these three cause 3,235 one-star reviews (36% of all one-stars). Each refused repeat
customer is a proven, low-risk borrower lost to a competitor, and public one-star reviews put off new users.

Goal (SMART): within 3 months of release, cut one-star reviews caused by the top 3 problems by 40%
(from 2.7% to 1.6% of all reviews - more cautious than the 60% fix rate in the model), and halve
"no new loan" complaints from customers who say they repaid.
Scope: product and communication changes inside the app. Changing who qualifies for credit is out of
scope; that is the risk team's decision. The product fix is explaining decisions, not overriding them.

## 2. Stakeholders (assumed)
| Stakeholder | Cares about | Needs from this project |
|---|---|---|
| Head of Product / Product manager | App rating, repeat-loan conversion, keeping good customers | Ranked problems with evidence and expected impact; what to build first and why |
| Engineering lead | Effort, app stability, release quality | Sized user stories; the CASHe 9.2.6 example as a reason for staged rollouts and release monitoring |
| Credit risk team | Defaults; not lending to risky borrowers | Assurance that the "no new loan" fix explains decisions without changing approval rules; agreed decline reasons that can be shown to users |
| Collections / recovery team | Collecting dues on time | Contact rules (allowed hours, call limits, never contacting a borrower's contacts) that still recover money |
| Customer support head | Ticket volume, time to resolve | Top complaint types with ready answers; fewer "why was I rejected" and "payment not updated" tickets |
| Compliance | RBI digital lending and fair recovery rules, clear fee disclosure | Proof that recovery, fee and data changes follow RBI rules (e.g. Key Facts Statement, calling hours) |
| Borrowers | Getting a loan when needed, fair charges, respectful treatment | A clear reason when declined, payments recorded fast, no harassment, no surprise charges |
## 3. Root causes (5 whys) for the top 3 issues
Note: Why 1-3 come from the review data [evidence]. Why 4-5 are my reasoning about internal causes
[hypothesis] and need to be confirmed with the product, risk, collections and payments teams.

### Issue 1: Rejected / no new loan without reason (2,280 reviews, 1,940 one-star)
- Why 1: Users leave 1-star reviews because they are refused a new loan or see no offer at all. [evidence]
- Why 2: It feels unfair because many repaid on time or closed early - ~32% say so; some were told closing
  early would raise their limit. [evidence]
- Why 3: They cannot understand the decision - the app shows only a generic message ("try after 2 months",
  "Sorry") with no reason and no next step, sometimes for months. [evidence]
- Why 4: Decisions come from an automated credit model and partner-lender rules, and the decline codes are
  not translated into reasons a user can understand. [hypothesis]
- Why 5: The app journey is built for first-time borrowers; the "declined repeat customer" journey has no
  owner and no metric. [hypothesis]
- Root cause: decline decisions are not explained, and repeat customers have no guided path back to eligibility.
- Supporting review quotes:
  - "If you do not provide services to customers who repay on time, what is the point of maintaining a good credit score?" (Moneyview, 1 star)
  - "got rejected by 2 years ago and showed try after 2 months. now 2 years passed ... still showing the same message" (1 star)

### Issue 2: Aggressive recovery calls (677 reviews, 97% one-star)
- Why 1: Users leave 1-star reviews about constant calls and messages from recovery agents. [evidence]
- Why 2: Calls start after only 1-5 days late, come many times a day, and reach family, contacts and
  workplaces. [evidence]
- Why 3: Agents use contact volume and social pressure as their main way to recover money. [evidence]
- Why 4: Collections is outsourced and measured mainly on money recovered, so more calls look like more
  effort. [hypothesis]
- Why 5: The calling system has no hard limits on calls per day, allowed hours or who may be contacted. [hypothesis]
- Root cause: incentives and tools reward contact volume, with no system-enforced contact rules.
- Supporting review quotes:
  - "if a borrower failes to pay emi for 5 days they start calling contacts" (1 star)
  - "6calls,sms 8,per day receiving very irritating" (1 star)

### Issue 3: Repayment problems (729 reviews, 87% one-star, most-agreed complaint)
- Why 1: Users leave 1-star reviews because they are penalised or shown as overdue despite paying. [evidence]
- Why 2: Payments are not updated in the app on time, auto-debit fails or runs on fixed dates, and the app
  is sometimes down on the EMI day. [evidence]
- Why 3: Borrowers cannot pay early - some apps have no manual "pay now" before the auto-debit date. [evidence]
- Why 4: Payments pass through several systems (UPI/auto-debit, partner lender, app) that sync in batches,
  not in real time. [hypothesis]
- Why 5: Late fees are applied automatically on the due date without checking whether a payment is pending
  or the app/auto-debit failed. [hypothesis]
- Root cause: penalties are applied by rule without checking payment status, and borrowers have no reliable
  way to pay early or prove payment.
- Supporting review quotes:
  - "I am paying my EMI on time every month, but I am still being charged a penalty of ₹590." (Moneyview, 1 star)
  - "Money View does not provide an option to manually pay the EMI before the scheduled auto-debit date" (Moneyview, 1 star)

## 4. Effort points (one line of reasoning each)

Scale (assumed, to validate with the engineering lead):
1 = text or setting change, days | 2 = one app screen, one team, 2-3 weeks |
3 = app + backend + another team (ops/policy), ~1 month | 4 = outside vendors or partner integrations |
5 = changes across partner lenders or banking rails, a quarter or more

| Issue | Effort (1-5) | Why |
|---|---|---|
| Rejected / no new loan | 2 | One new screen showing the main decline reason and the reapply date; reasons come from decline codes the risk team already has, so the credit model does not change (becomes 3 if decline codes are not stored) |
| Hidden charges | 2 | One "total cost" screen before e-sign; the numbers already exist in the Key Facts Statement |
| App bugs / crashes | 2 | Crash monitoring and staged rollouts are standard tools; mostly a release-process change |
| Customer support | 3 | In-app ticket tracking and callback booking need a helpdesk integration plus staffing changes |
| Recovery calls | 3 | Mostly policy and calling-system rules (call caps, allowed hours, no calls to contacts), but outside agencies need retraining and audits |
| Repayment problems | 3 | "Pay now" and auto-debit retry are app + payments-backend work; updating payments within 48 hours needs reconciliation with partner lenders |
| KYC & documents | 4 | Depends on external KYC providers and DigiLocker integration; low volume (65 reviews) so it can wait anyway |
| Disbursal delay | 5 | A tracker screen is easy, but actually speeding up disbursal depends on partner banks and payment rails |
## 5. User stories (2 per top issue)
Format: As a <user>, I want <action>, so that <benefit>. Acceptance criteria are written as Given / When / Then.
Numbers marked (assumed) are starting proposals to agree with the relevant team.

### Issue 1: Rejected / no new loan without reason
**US1.1** As a repeat borrower who repaid on time, I want to see the main reason my new loan was declined and
when I can reapply, so that I know what to do instead of guessing.
- Given my application is declined, when the decline screen opens, then it shows one main reason in plain
  language from a list approved by the risk and compliance teams (no internal scores shown).
- Given I am declined, then the screen shows a specific reapply date, and after that date I can reapply or
  I get a new reason - never the same "try after 2 months" message again and again.
- Given the screen is live, then "no new loan" complaints from customers who say they repaid are tracked
  monthly (keyword query B4).

**US1.2** As a borrower thinking of closing my loan early, I want to know before I foreclose whether it
affects my next loan offer, so that I don't close early expecting a higher limit that never comes.
- Given I open the foreclose screen, when I have a pre-approved offer, then the app shows whether that
  offer stays valid after I foreclose.
- Given no future loan is guaranteed, then the screen says so clearly before I confirm.

### Issue 2: Aggressive recovery calls
**US2.1** As a borrower who is a few days late, I want recovery contact to be limited and respectful, so that
I am not harassed while I arrange payment.
- Given my loan is overdue, when any agent or the calling system schedules a call, then calls are blocked
  before 8:00 and after 19:00 and capped at 3 per day (assumed, set with compliance).
- Given my loan, then the calling system only allows my own number - calls to my contacts are blocked.
- Given any recovery call is made, then it is logged with time and agent ID for audit.

**US2.2** As a borrower, I want a "report a recovery call" button in the app, so that abusive calls are
stopped and investigated.
- Given I report a call, when I submit, then a ticket is created and acknowledged within 24 hours.
- Given a complaint is confirmed, then the agent is removed from my account and the case appears in the
  monthly compliance report.

### Issue 3: Repayment problems
**US3.1** As a borrower, I want to pay my EMI myself before the auto-debit date, so that I can pay when I
have the money and avoid failed auto-debits.
- Given my EMI is due within 7 days, when I open my loan screen, then a "Pay now" (UPI) button is available.
- Given my payment succeeds, then the auto-debit for that EMI is cancelled and the EMI shows as paid within
  2 hours (assumed).
- Given my bank shows the payment but the app does not, then I can upload proof and the EMI shows
  "payment under review", which stops late fees.

**US3.2** As a borrower, I want no late fee when my payment was pending or the app or auto-debit failed,
so that I am not punished for the company's technical problem.
- Given the due date, when an auto-debit fails for a technical reason, then it is retried at least once
  before any late fee is applied.
- Given the app had a logged outage on the due date, then late fees for that day are waived automatically.
- Given a late fee was charged wrongly, then it is reversed within 3 working days and the payment is
  reported to credit bureaus as on time.
## 6. KPIs to track after each fix
"Today" comes from the 121,688 reviews (May-Nov 2026). Review KPIs are measured monthly with this pipeline,
comparing the same apps and the same length of time before and after each release. Reviews come from only
some users, so each fix also has an internal KPI that needs company data.

| Fix | KPI | Today | Target (3 months after release) |
|---|---|---|---|
| Explain declines + reapply date | One-star "no new loan" reviews per 1,000 reviews | 15.9 | 9.6 (-40%) |
| Explain declines + reapply date | "No new loan" complaints from customers who say they repaid, per 1,000 reviews | 8.0 | 4.0 (halved) |
| Explain declines + reapply date | Repeat customers who reapply after a decline (internal) | needs company data | baseline first, then +10% (assumed) |
| Recovery contact rules | One-star recovery-call reviews per 1,000 reviews | 5.4 | 2.7 (halved - compliance risk) |
| Recovery contact rules | Recovery calls outside 8:00-19:00 or to a borrower's contacts (internal) | needs company data | 0 |
| Repayment fixes | One-star repayment reviews per 1,000 reviews | 5.2 | 3.1 (-40%) |
| Repayment fixes | Payments shown as paid within 2 hours (internal) | needs company data | 99% (assumed) |
| All three | One-star reviews from the top 3 problems, per 1,000 reviews | 26.6 | 16.0 (-40%, the goal in section 1) |
| Health check | Happy reviews per day, per app (catches a CASHe-style drop early) | track | no sudden fall of 30%+ |

Guardrails (must NOT get worse):
- Default rate on repeat loans (risk team) - the decline fix explains decisions, it does not change them
- Money recovered within 30 days of the due date (collections) - contact rules must not hurt recovery
- Late-fee income is allowed to fall only by fees that were charged wrongly

## 7. 3-month roadmap

Order = rating gain / effort (section 4 + the pipeline's roadmap), with one exception: recovery-call rules
move up because breaking RBI recovery rules is a legal risk, whatever the score.

- Month 1 (quick wins + compliance must-do):
  - No new loan: decline reason + reapply date screen (US1.1) and foreclosure warning (US1.2)
    -> #1 priority: +0.037 stars, effort 2. Week 1: agree the decline-reason list with the risk team.
  - App bugs: crash monitoring + staged rollouts + 48-hour hotfix rule (#2 priority: +0.010 stars, effort 2)
  - Recovery calls, policy part: calling hours 8:00-19:00, max 3 calls a day, no calls to contacts,
    written to all recovery agencies (compliance must-do; system enforcement follows in month 2)

- Month 2 (medium, effort 3):
  - Repayment: "Pay now" before auto-debit, auto-debit retry before any late fee, no fee on a logged
    outage (US3.1, US3.2) -> #3 priority: +0.012 stars
  - Recovery calls, system part: limits enforced in the calling system + "report a recovery call" button (US2.1, US2.2)
  - Hidden charges: one "total cost" screen before e-sign (effort 2, linked to the Key Facts Statement rule)

- Month 3 (bigger projects + measure):
  - Customer support: in-app ticket tracking and callback booking (effort 3)
  - Disbursal delay: live tracker screen only; speeding up partner banks is a later, effort-5 project
  - Rerun this analysis on the new reviews and compare every KPI in section 6 against its target
  - KYC: deferred - only 65 reviews and effort 4

App-specific focus (finding 6): KreditBee -> "no new loan" first; Moneyview -> app stability first;
CASHe -> disbursal speed and hidden charges first; Fibe -> repayment experience (its biggest complaint share).

Dependencies and risks:
- Risk team must approve the decline-reason list (blocks the #1 fix)
- Recovery agencies must be retrained and audited (outside the company's direct control)
- Partner lenders must support faster payment updates (could delay month 2)
## 8. Recommendation memo (one page, to the Head of Product)
To: Head of Product, digital lending app
From: Sharan, Business & Data Analyst
Date: 25 November 2026
Subject: Fix three problems to cut one-star reviews by 40% in 3 months

Recommendation
Approve a 3-month plan that fixes three problems: unexplained loan refusals, aggressive recovery calls and
repayment errors. Together they cause 36% of all one-star reviews. Start with the refusal screen: it is the
biggest win (+0.037 stars) for one of the smallest efforts (one screen, ~3 weeks).

What I found (121,688 Google Play reviews of KreditBee, Moneyview, Fibe and CASHe, May-Nov 2026)
1. Only 4.8% of reviews name a specific problem, but they cause over half of all 8,979 one-star reviews.
   The 4.6-star average hides this.
2. "Rejected / no new loan" is the #1 problem: 1,940 one-star reviews (22%). About 1 in 3 of these
   complainers say they had already repaid - these are proven, low-risk customers we are losing.
3. Repayment errors (payments not recorded, late fees despite paying) are the complaint other users agree
   with most (4.2 "helpful" votes per review). Recovery calls are the angriest (97% one-star) and a
   regulatory risk under RBI recovery rules.
4. Watch review volume, not only the rating: CASHe's rating fell from 3.72 to 2.49 after one release because
   happy users stopped reviewing (-72%), while complaints did not change at all.

What I recommend
- Month 1: show the decline reason and a reapply date (approval rules unchanged); crash monitoring and staged
  rollouts; written recovery-calling rules for all agencies (8:00-19:00 only, max 3 calls a day, no contacts).
- Month 2: "Pay now" before auto-debit and no late fee when our systems fail; enforce calling limits in the
  system; one "total cost" screen before e-sign.
- Month 3: support ticket tracking, a disbursal tracker, and a re-run of this analysis to measure results.

Expected impact
If 60% of affected users are satisfied after the fixes, about 1,940 fewer one-star reviews over a similar
period. My target is more cautious: -40% one-star reviews from these three problems (2.7% -> 1.6% of reviews).

What I need from you
- Approval of the Month 1 scope
- One week of the risk team's time to agree the list of decline reasons users can see
- Access to internal data (repeat applications, call logs, payment-update times) to track the internal KPIs

Limits of this analysis
Reviews come from a vocal minority, so they show what hurts, not how many customers it affects. Issue labels
come from an AI model (91.8% accurate on 500 checked reviews). Causes beyond what reviews say are hypotheses
to confirm with the teams involved.