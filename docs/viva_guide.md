# Explaining and defending the project

**What does it do?** It orders feasible crossing-improvement packages for review, using demand, vehicle exposure and observed deficiencies. The destination extension tests a further access consideration.

**What is fuzzy?** A triangle records a lower, central and upper value. Repeated counts and assessor disagreement motivate the range. The triangular membership shape is an approximation; membership is not probability.

**Why TOPSIS?** It makes the trade-offs inspectable by comparing each candidate to high- and low-priority ideal profiles. Its suitability is a modelling argument, not proof of superior accuracy.

**What did you change from Chen?** The distance core is Chen-style, but observed outer-bound scaling, crisp weights and weighted ideals are declared adaptations. Do not call this an exact reproduction of the original paper.

**Why equal weights?** No stakeholder elicitation was performed. Equal weights are transparent and provisional. The sensitivity experiment checks a limited range of alternatives rather than inventing expert opinions.

**What are the actual findings?** The synthetic example runs successfully. A leads the base model; C leads the destination extension. A leads 864 of 1,000 bounded weight draws. These are computational demonstration results, not campus findings.

**Does fuzziness always change the outcome?** No. Contracting the widths in this example keeps A first but changes lower ranks. With zero width and these ideals, the model reduces to the equal-weight central-value baseline after consistent scaling.

**What is the extension's contribution?** It operationalises a specific question about essential access and compares the resulting order. A changed winner does not prove a better decision.

**What validates the project?** Independent arithmetic and automated tests check implementation. Baseline and sensitivity comparisons check behaviour. Independent site review is still pending and cannot be replaced by agreement between algorithms.

**What happens with ties or missing data?** Missing measurements cause an error. Exact ties share a rank; ID order makes displays deterministic. Top-k summaries use that order, so tied boundaries need care.

**Can we recommend construction now?** No actual crossing survey is included. Gather evidence, obtain feasibility and independent review, and consider cost and dependencies before making a real recommendation.

## Demonstration sequence

Run the demo, open base_ranking, then calculation_trace, extension_ranking and uncertainty_sensitivity under the hypothetical prefix. Explain one row using docs/worked_example.md. Show the run manifest and test results. Finish by showing the empty field forms and describing exactly what must be collected.
