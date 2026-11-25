# Findings

Data: 121,688 Google Play reviews of 4 Indian loan apps (CASHe from 1 May 2026; KreditBee from 23 Jun,
Fibe from 14 Jul, Moneyview from 30 Jul; all up to 21 Nov 2026). Each review was labelled by hand (2,000),
by a rule for 1-2 word reviews (75,509) or by the AI model (46,179).

## Key findings (number + so what)

1. Most reviews are happy, so problems hide in a small share. 91% of reviews are positive; only 5,874 (4.8%)
   name a specific problem. The biggest is "rejected / no new loan without reason": 2,280 reviews
   (39% of specific complaints), 85% of them 1-star.
   So what: the 4.6-star average hides the problems; analyse the complaints, not the average.

2. Some problems make users far angrier than others. Recovery calls: 97% 1-star (avg 1.03 stars);
   customer support 91%; repayment and disbursal delay 87%. App bugs and hidden charges are the mildest
   (avg 2.2 stars, 55-61% 1-star).
   So what: severity matters as much as volume when choosing what to fix.
   Caution: the model uses the star rating, so these shares are partly circular; to be confirmed on hand labels.

3. Eight named problems explain about half (53%) of all 8,979 one-star reviews. "No new loan" alone causes
   1,940 (22%, about 1 in 5), almost 3x the next problem. The top 3 (no new loan, recovery calls,
   repayment & credit score) cause 3,235 (36%). KYC causes only 31.
   If a fix satisfies 60% of affected users (assumption; 40-80% gives ~780-1,550), fixing "no new loan"
   alone would prevent ~1,160 one-star reviews; the top 3 together ~1,940.
   So what: fix "no new loan" first; KYC improvements can wait.

4. Many "no new loan" complaints come from existing customers. 972 of the 2,280 (42.6%) contain
   repaid / closed / new-loan keywords. A manual check of 20 random matches found 15 truly repeat customers
   (75%), so roughly 730 (~32%) are customers who say they repaid and were then refused (with only 20
   checked: about 23-38%). KreditBee has the most (603 of 1,259 = 47.9%), then Moneyview (43.9%);
   Fibe and CASHe ~25%.
   So what: show repeat customers why they were declined and how to qualify ("path to your next loan"
   screen), and pre-approve customers with a clean repayment record.

5. Users agree most with repayment complaints. They get 4.2 "helpful" votes per review (3,071 votes on
   729 reviews) vs 1.5 for "no new loan", and the agreement is broad: 73 of them got 10+ votes (more than
   any other issue) and the top 5 reviews hold only 26% of the votes. The top-voted ones are about payments
   not being updated, penalties despite paying on time, and the app being down on EMI day.
   Disbursal delay is close (4.8 per review) but more concentrated (43% of its votes from 5 reviews).
   Recovery calls, app bugs and hidden charges get under 1 vote per review.
   So what: fix the basics of repaying - record payments fast, never charge a penalty when the auto-debit
   or the app failed, keep EMI payment working - and keep it in the top 3 of the roadmap.
   Limitations: older reviews have had more time to collect votes.

6. Apps differ a lot. Specific complaints are 27% of CASHe's reviews, vs about 6% for KreditBee and Moneyview
   and 2% for Fibe; CASHe has the highest rate on every one of the 8 problems. CASHe's one-star reviews are
   driven far more by disbursal delay (14% of its one-stars vs 3.7% across all apps) and hidden charges
   (8.7% vs 4.0%). KreditBee's biggest problem is "no new loan" (3.2% of its reviews, 1,259 reviews - the
   most of any app). Moneyview stands out for app bugs (1.4% of its reviews vs 0.2-0.3% at Fibe and KreditBee).
   Fibe is the cleanest (2.2%).
   So what: one roadmap does not fit every app - CASHe should fix disbursal speed and charges, KreditBee its
   "no new loan" experience, Moneyview app stability.

7. CASHe's rating fell from 3.65 (June) to 2.21 (August 2026), right after version 9.2.6 (first seen
   17 July): 3.72 -> 2.49 stars in the 30 days before vs after (Welch t-test p < 0.001, Cohen's d = -0.67,
   a medium-to-large effect), confirmed by an independent SQL query. But complaints did NOT rise (65 -> 65
   reviews); happy reviews collapsed (231 -> 64, -72%). Control: KreditBee, the only other app with data on
   both sides, stayed steady (~255 happy reviews and ~15 complaints a day, before and after). So the drop is
   CASHe-specific and comes from losing satisfied users' reviews, not from new problems. Likely causes
   (reviews alone can't prove which): fewer new borrowers, or the app stopped asking happy users to rate it.
   CASHe only partly recovered (~2.85 by Oct-Nov).
   So what: track review volume next to the star rating, and check what 9.2.6 changed (rating prompt,
   approval rules) before blaming bugs.

8. Only 3 app versions passed the release test (newer than all previous versions, 30+ reviews, a full
   30 days of data on both sides). Besides CASHe 9.2.6, Fibe 3.6.9 (4.89 -> 4.75) and 3.7.3
   (4.76 -> 4.55) also had p < 0.001, but moved the rating by only 0.1-0.2 stars (Cohen's d = ___
   and ___). With thousands of reviews, even tiny changes become "significant".
   So what: judge a release by effect size, not p-value; only CASHe 9.2.6 was a real problem.

   9. Copied reviews exist but are rare: among long reviews (15+ words), 59 texts appear more than once,
   140 extra copies in total (0.1% of all reviews), so they don't change any finding. Most are praise
   on Fibe (the top text appears 42 times on Fibe and KreditBee), and some read like marketing or
   AI-written summaries ("users are saying they enjoy the fast, paperless loan process").
   A few complaints were also posted on several apps.
   So what: star ratings can include templated praise, and exact copies are only the ones that can be
   detected, so treat a single app's rating with care. I kept the copies (I can't prove they are fake)
   and report them instead of deleting them.

## Voice of the customer
- (quotes to add)

## AI model
- Model: TF-IDF (words + character pieces) + star rating -> Logistic Regression, trained on 1,500 labelled reviews
- Accuracy on 500 test reviews: 91.8%   (baseline, always guessing "positive": 78.8%)
- Macro F1: 0.669
- "No new loan": precision 77%, recall 75% (text-only model: 62% / 78%)
- Improvement story: error analysis showed the text-only model (87.6%) calling happy 5-star reviews that
  mention "loan" a "no new loan" complaint; adding the star rating as a feature fixed most of them.
- - Labels: drafted with AI assistance; I reviewed the 47 most uncertain test labels myself and kept 3 corrections.
- Still weak: the smallest classes (customer support, KYC, disbursal delay) have only 2-4 test reviews
  each, so their scores are unreliable.

## Statistics
- Chi-square (issue x rating group): chi2 = __, df = 18, p < 0.001, Cramer's V = 0.69.
  Caution: partly circular - short reviews are labelled from their stars and the model also uses the stars -
  so this describes the data rather than proving a link. Severity is checked on hand labels (to do).

## SQL answers
1. Issue share and rating (B1): finding 1 and 2
2. Which app suffers most from each issue (B3): finding 6
3. Monthly rating change (C1): CASHe 3.65 (Jun) -> 2.21 (Aug) -> ~2.85 (Oct-Nov); other apps: __
4. Rising issues (C3): __
5. Release before/after (D1): same 3 releases as Python, numbers match exactly
6. Most-agreed complaints (B5, B7): finding 5
7. Model agreement on test set (E2): __
8. Reviews to label next (E3): __
9. Roadmap (F1): #1 No new loan +0.036 stars (effort 2), #2 App bugs +0.009 (effort 2),
   #3 Repayment & credit score +0.012 (effort 3); average 4.63 -> 4.69 if the top 3 are fixed at 60%
10. Model runs (E1): __
11. Repeat customers (B4 + manual check of 20): finding 4
12. One-star reviews a fix could prevent (F2, F3): findings 3 and 6
13. CASHe before/after 9.2.6 + control check (C4, C5): finding 7