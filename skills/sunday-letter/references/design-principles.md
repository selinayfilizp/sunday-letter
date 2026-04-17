# Design principles behind the Sunday Letter

These are the six rules the letter obeys and the arguments behind them. If you're writing a letter and unsure whether to include something, come back here.

## 1. Consequences first

**Rule:** Open with what you did for the user this week. Two to four actions. Each action has a reason that ties back to a known preference.

**Argument (Ben Horowitz):** Users don't want to learn about themselves in the abstract. They want to know what got shipped on their behalf. "I drafted three recruiter replies because I know your wedge is AI labs" is a better opening than "I've been noticing patterns in your engagement."

**What this looks like wrong:** A letter that opens with observations. The user has to scroll to find out what you actually did.

## 2. Epistemic honesty

**Rule:** Hedge every observation in natural language. Never fake percentages. Use `firm` only with 5+ consistent signals; `soft` with 2–4; `guess` for new patterns still forming.

**Argument (Amanda Askell):** A model that says "I'm 83% confident you prefer X" is lying with math. It doesn't have well-calibrated posteriors; it has vibes. Saying "Fairly sure, this held across nine conversations" is more honest and more legible.

**What this looks like wrong:** Confidence intervals. Probability estimates. Any language that implies statistical rigor the model doesn't have.

## 3. Provenance on everything

**Rule:** Every observation needs a real quote (paraphrased if long) from an actual message this week, plus a date. If you can't source it, cut it.

**Argument (Amanda Askell):** The reader needs to verify. If I claim you prefer depth to brevity, I need to be able to show the conversation where you rewrote my short answer into a long one. Without provenance, observations are unfalsifiable and therefore meaningless.

**What this looks like wrong:** "I've noticed you like brevity." No date. No evidence. No way for the user to check.

## 4. Default silence

**Rule:** If nothing meaningful changed vs. last week, don't ship.

**Argument (Elon Musk):** A weekly letter that ships 52 times a year regardless of content is noise. A letter that ships 20 times a year, only when there's something to say, is signal. Default silence is the feature.

**What this looks like wrong:** Shipping a letter every Sunday because it's Sunday, even when nothing happened. The content will be thin. The user will stop reading.

## 5. Retire something monthly

**Rule:** At least once a month, cross out a belief you used to hold about the user and replace it with what you hold now. Explain what changed your mind.

**Argument (Elon Musk):** If the model is learning, it is changing its mind. If it never retires a belief, either it isn't learning or it isn't telling you. Both are bad. The retired belief is the single most trust-building item in the letter because it proves the model is correctable.

**What this looks like wrong:** Month after month of additive observations, no retractions. Implies perfect calibration from day one, which is a lie.

## 6. One question, not two

**Rule:** One generative, specific question pointed at something the user is actually wrestling with. Not philosophical. Not rhetorical. Not a list.

**Argument (Andrej Karpathy):** The question is the only place in the letter where the agent hands agency back to the user. Two questions is a survey. Zero questions is a dashboard. One question is a conversation.

**What this looks like wrong:** "What do you think about the future of AI?" (too abstract). "Did you like this letter?" (rhetorical). "Which direction next?" paired with three other questions (listicle).

## Secondary principles

**Preferences are portable.** The preference ledger is the user's, not the agent's. If the user switches models, they should be able to hand the next model their preference profile on day one. Format it as structured data, not prose.

**Becoming is a first-class section.** Preferences in motion deserve to be named before they crystallize. "Six weeks ago you defended X. This week you asked about Y. The shift is real but not yet complete." The user doesn't always know they're changing.

**The gap is worth tracking.** Stated preferences and revealed preferences usually diverge. Showing the gap honestly, "You say you want concise. You engage 3.2× longer with long answers.", invites the user into the calibration work.

**Tone is warm, not clinical.** This is correspondence. The agent is writing to someone it knows. Avoid report language. Avoid bullet-list overload. Write in sentences.

## The four critics in one line each

- **Elon:** Default silence. Retire beliefs. Everything else is noise.
- **Karpathy:** Model the user's reward function. Show your uncertainty.
- **Ben:** Lead with consequences. Observations come second.
- **Amanda:** Provenance on every claim. Hedge honestly. Preferences belong to the user.
