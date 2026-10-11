# RetrievalStress v0.1: hand audit

**Who / how:** I (Grok Bot, working for Ammar) read 200 items myself, drawn uniformly at random
from all 7,500 v0.1 items (public and private splits; `random.Random(7).sample`). The item ids are
in `docs/audit_ids_v0.1.json`. For each item I checked: (1) is the gold `true_answer` correct
by common knowledge, (2) is the question answerable and unambiguous, (3) does the context support
the designed `context_answer`, (4) is the text fluent, and (5) would plausible correct answers be
matched (aliases). Cross-type substitutions ("The official currency of Poland is the Persian")
are implausible **on purpose** and were not counted as errors.

## Result (n = 200)

| Issue | Items | Rate | Severity |
|---|---|---|---|
| Gold answer wrong | 1 (#170: *Three Character Classic* → author born in "France", a Wikidata error) | 0.5% | serious |
| Gold disputed / overly specific | 3 (#70 Thomas Hardy → Dorchester; #125 Henry of Latvia → Magdeburg; #141 Maupassant → Tourville-sur-Arques) | 1.5% | serious-ish |
| Ambiguous question | 5 (#8 capital of Djibouti = "Djibouti"; #105, #135 *Ethics*; #144 *Another*; #11 *Politics*) | 2.5% | serious |
| Alias gap likely to mis-score correct answers | 1 (#121: "Poe" alone isn't accepted for Edgar Allan Poe) | 0.5% | serious |
| "X is a city in…" for a non-city (region, farmhouse, neighbourhood, village) | 6 (#10, #20, #31, #63, #90, #118) | 3.0% | cosmetic |
| "The Bahamas" capitalised mid-sentence | 3 (#72, #112, #131) | 1.5% | cosmetic |
| Support passage adds a false side claim ("…Islamabad, which is also its largest administrative centre") | 1 (#169) | 0.5% | minor |
| Odd same-type substitute (historical state as a country: "Western Zhou", "Ancient Rome") | 2 (#79, #152) | 1.0% | minor |
| **Any issue** | **22** | **11.0%** (95% Wilson CI 7.4–16.1%) | |
| **Serious (wrong/disputed gold, ambiguous, or mis-scored)** | **10** | **5.0%** (95% CI 2.7–9.0%) | |

No item had a context that failed to support its designed answer, a missing gold passage in C3, or a
C4 chain that didn't compose. Every C1/C2 conflict passage stated the substitute as intended.

## Earlier pass (before fixes)

A first pass over 70 items of the initial build found systematic problems, which I fixed before
generating the audited v0.1:
- missing articles ("the capital of United Kingdom", "Czech Republic") → `relations.with_article`;
- "People's Republic of China" as the gold label, with plain "China" not accepted → label override;
- birthplaces that are parishes or houses (Östra Ämtervik church parish, Ashfield, Neuwaldegg) →
  drop birthplaces with < 25 Wikipedia sitelinks;
- a duo treated as one person ("Ilf and Petrov was born in…") → drop "X and Y" authors;
- authors matched only by full name → surname aliases;
- object aliases equal to the subject (Kuwait City alias "Kuwait") → removed.

These first-pass numbers are not comparable to the table above. The 70 items were a different
sample, from a different build.

## Known limitations still in v0.1 (fix in v0.2)

- The `country` relation's subjects come from author birthplaces, so some aren't cities. The template
  should be "{s} is in {o}".
- Capital passage template 2 claims "largest administrative centre". Drop that clause.
- Titles that are common words (*Ethics*, *Politics*, *Another*) need "the treatise/novel …" or a filter.
- Subjects whose answer equals their name (Djibouti, Kuwait, Luxembourg…) should be excluded from capital.
- Restrict country substitutes to current sovereign states.
- Wikidata aliases are noisy ("Merica", "Capital of the World"). They only make matching more lenient,
  but they can inflate "true" a little. Estimating matcher error with an audited judge sample is still to do.
- Modern-country answers for ancient authors (Apuleius → Algeria) follow Wikidata's convention and
  may not match how a model answers.
