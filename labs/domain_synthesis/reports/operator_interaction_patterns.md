# GPT Export Operator Interaction Patterns

## Scope
- Message index: `domains/self/data/gpt_history/messages_index.jsonl`
- Raw fallback: `archive/chat_exports/chatgpt/chat.html`
- User messages scanned: 1441
- Conversations classified: 110

## High-Authority Interaction Patterns
- Direct corrections found: 208
- Negative-control/rejection markers found: 20
- Compression/flattening markers found: 7
- Artifact-generation markers found: 70
- Social-friction markers found: 19

## Correction Style
The operator corrects by narrowing boundaries, preserving exact wording when it carries structure, and rejecting clean summaries that lose evidence doors.

## Compression Risk
The recurring risk is not length; it is losing re-openability. Cleaner language is treated as failure when it erases examples, gates, or old evidence.

## Prompt / Interaction Style
Requests often arrive as operational constraints: read order, outputs, validation, privacy gates, path contracts, and explicit non-promotion rules. Iteration is used to sharpen the work rather than merely repeat it.

## Manual Review Seeds
- `language` 2026-02-07T01:57:41.853000+00:00: "im trying to become fluent in spanish but its hard for me to create sentences even since most of my vocabulary are nouns and i need verbs and connecting words (like hay, lo, se, ves). im currently speaking to native spea"
- `language` 2026-02-07T04:22:04.598000+00:00: "sorry wasnt finished 1. i forgot to (do something) because there wasnt any time 2. one states a problem exist while the other one is explicitly described as big, implying its just been realized 3. bascially describing it"
- `language` 2026-02-07T04:27:40.438000+00:00: "ok now questions from me. can se be used for any verb? what are the most common ones if not? when do i use "que" as a connector gap when its not used like "what" or "that". explain algo que and tengo que. "lo ven pero no"
- `body_sensory` 2026-02-07T05:27:20.750000+00:00: "no apointments until march? i figured nobody is going"
- `attraction` 2026-02-07T05:50:43.673000+00:00: "and i can just go to a library for photocopies of my BC and license? i thought everything would be on sight but i have a month to prep for this so no biggie"
- `sports` 2026-02-09T04:31:13.709000+00:00: "no, colspan should change too. just the NFL names/links to UFL"
- `wiki` 2026-02-09T04:45:28.653000+00:00: "no keep the rendered formatting (so nothing changes to a reader). but i want cleaner code here"
- `wiki` 2026-02-09T04:51:40.149000+00:00: "no the numbered i need adjusted since division and league were added and the labels below must be +2"
- `language` 2026-02-09T05:58:30.428000+00:00: "yes it already does feel like that spatially. just how state/connection/conditional it is, i actually really prefer that over english which is more of a pipeline where order is most important"
- `language` 2026-02-09T06:01:22.097000+00:00: ""Most learners fight Spanish because they try to push it through an English parser." im doing this but only because my mind has 30 years of only cognating (is that a word) in english. its actually more frustrating to be "
- `language` 2026-02-09T06:15:47.556000+00:00: "language learning is like the most extreme example of a declarative–procedural shift. "When people say “it just clicked,” what actually happened is:" oh how i await the day. some people say it happens and they dont even "
- `language` 2026-02-09T06:20:39.036000+00:00: "what are some things i could reasonable expect by 6 months, assuming no real breaks (few days every know and then are actually good for anti burnout)"
- `language` 2026-02-09T06:42:33.649000+00:00: "this actually helps way more than any table can explain it. but first i need to get all the present verbs of the top 10 most common verbs locked in first. lets start with ser"
- `language` 2026-02-09T15:16:36.420650+00:00: "Which latino or hispanic in the spanish speaking world known mostly for them actually is fluent in English and it surprises even spanish speakers."
- `language` 2026-02-09T15:22:17.227153+00:00: "No, but it does help knowing that some of them learn late. I'm in my early thirties now. It seems very late."
- `language` 2026-02-09T16:31:57.789057+00:00: "The difference between me olvide and no me acuerdo"
- `language` 2026-02-09T16:35:45.492950+00:00: "No lo hago."
- `language` 2026-02-09T16:36:54.524728+00:00: "No puedo hacerlo."
- `language` 2026-02-09T16:40:48.840297+00:00: "no puedo hablarlo muy bueno."
- `language` 2026-02-09T16:42:17.507600+00:00: "Vedon ascoltarlo, pero no hablato."
