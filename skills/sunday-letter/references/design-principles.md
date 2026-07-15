# Design principles behind the Sunday Letter

These are the six rules the letter obeys and the arguments behind them. If you're writing a letter and unsure whether to include something, come back here.

## 1. Consequences first

**Rule:** Open with what you did for the user this week. Two to four actions. Each action has a reason that ties back to a known preference.

**Rationale:** Users do not need an abstract personality report before they know what actually happened. "I drafted three replies because you asked me to protect your focus time" is a better opening than "I've been noticing patterns in your engagement."

**What this looks like wrong:** A letter that opens with observations. The user has to scroll to find out what you actually did.

## 2. Epistemic honesty

**Rule:** Hedge every observation in natural language. Never fake percentages. Use `firm` only with 5+ consistent signals; `soft` with 2–4; `guess` for new patterns still forming.

**Rationale:** A model that says "I'm 83% confident you prefer X" is implying measurement it does not have. Saying "Fairly sure, this held across nine conversations" is more honest and more legible.

**What this looks like wrong:** Confidence intervals. Probability estimates. Any language that implies statistical rigor the model doesn't have.

## 3. Provenance on everything

**Rule:** Every observation needs a real quote (paraphrased if long) from an actual message this week, plus a date. If you can't source it, cut it.

**Rationale:** The reader needs to verify. If the agent claims the user prefers depth to brevity, it needs to identify the dated conversation where the user expanded a short answer. Without provenance, observations are unfalsifiable.

**What this looks like wrong:** "I've noticed you like brevity." No date. No evidence. No way for the user to check.

## 4. Default silence

**Rule:** If nothing meaningful changed vs. last week, don't ship.

**Rationale:** A weekly letter that ships regardless of content becomes noise. A letter that ships only when there is something to say remains signal. Default silence is the feature.

**What this looks like wrong:** Shipping a letter every Sunday because it's Sunday, even when nothing happened. The content will be thin. The user will stop reading.

## 5. Retire something monthly

**Rule:** At least once a month, cross out a belief you used to hold about the user and replace it with what you hold now. Explain what changed your mind.

**Rationale:** If the model is learning, it sometimes changes its mind. A retired belief is trust-building because it proves the model is correctable. The ledger must show that the belief was actually held before it can be retired.

**What this looks like wrong:** Month after month of additive observations, no retractions. Implies perfect calibration from day one, which is a lie.

## 6. One question, not two

**Rule:** One generative, specific question pointed at something the user is actually wrestling with. Not philosophical. Not rhetorical. Not a list.

**Rationale:** The question is where the agent hands agency back to the user. Two questions is a survey. Zero questions makes the note feel like a dashboard. One question keeps it a conversation.

**What this looks like wrong:** "What do you think about the future of AI?" (too abstract). "Did you like this letter?" (rhetorical). "Which direction next?" paired with three other questions (listicle).

## Secondary principles

**The ledger belongs to the user.** It stays in the local Sunday Letter archive as structured data. Cross-agent profile export is a future capability, not a current claim.

**Becoming is a first-class section.** Preferences in motion deserve to be named before they crystallize. "Six weeks ago you defended X. This week you asked about Y. The shift is real but not yet complete." The user doesn't always know they're changing.

**The gap is worth tracking when it is observable.** Showing "You asked for concise, then expanded the same answer through four revisions" is grounded in conversation history. Do not invent engagement telemetry the collector cannot see.

**Tone is warm, not clinical.** This is correspondence. The agent is writing to someone it knows. Avoid report language. Avoid bullet-list overload. Write in sentences.

## Product boundary

These principles describe the letter's editorial behavior. They do not imply
background tracking, remote delivery, or access to data outside the selected
local Codex conversation bundle.
