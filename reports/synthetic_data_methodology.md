# Public-source-informed synthetic crossing-priority dataset

## Purpose and evidence boundary

This dataset demonstrates fuzzy TOPSIS near IIIT Kottayam, Kerala. **Every criterion
score, fuzzy interval, improvement package and resulting priority is synthetic.**
It contains no field counts, measured speeds, field photographs, audited
deficiencies, independently validated crossing inventory, or engineering
feasibility assessment. Public map features are observations of what is mapped,
not ground truth about current conditions. It is not an empirically validated
pedestrian-safety ranking and cannot replace the actual-data submission requirement
without instructor approval.

The original four-row `hypothetical_demo.csv`, original field-input conventions,
and TOPSIS arithmetic remain separate and unchanged. This dataset uses an explicit
`--synthetic-input` mode; do not pass it as field observations using `--input`.

## Sources and preservation

`data/source_inventory.csv` records source URLs, retrieval dates, geographic
coverage, available fields, uses, licenses, saved bodies and checksums. The actual
OpenStreetMap response, Overpass query and metadata are under `data/raw/`.
Government portals and accessible research resources are preserved under
`data/raw/public_sources/`; see `research_notes.md` there for inspection results
and unavailable resources. Catalogue pages alone are not measured traffic data.
No aggregate crash statistic is converted into crossing-level counts or scores.

Substantive contextual resource inspected: NATPAC's
[Draft Road Safety Vision—Kerala](https://natpac.kerala.gov.in/wp-content/uploads/2023/08/Draft-Road-Safety-Vision.pdf).
Its printed page 12 discusses sidewalks, pedestrian crossings and pedestrian
safety; page 13 discusses lighting and road markings. The downloaded PDF has
68 pages, repeating the 34-page document. Its historical state/district statistics
are not contemporary crossing-level observations and are not used to calibrate
these scores. The separate NATPAC `Booklets-1.pdf` is only a publication-title
catalogue, not the contents of a Pedestrian Safety Guide.

The **only numeric geographic inputs to the generator are the preserved OSM
extract**. Government/research resources supply context and evidence boundaries,
not numerical calibration, unless a future documented version explicitly changes
this. Portal availability must not be confused with having acquired local counts.

Mapped campus identity/center comes from the saved Nominatim result for OSM way
1077351803, at latitude 9.7554364, longitude 76.6495350. This is a mapped center,
not a surveyed gate position. The official institute website is contextual evidence
only. OSM data attribution: © OpenStreetMap contributors, available under
[ODbL 1.0](https://www.openstreetmap.org/copyright). Retain that attribution and
check applicable database redistribution obligations when publishing derivatives.

## Candidate selection: real coordinates, hypothetical crossings

The preserved successful extract has 431 elements and bounds
`[9.7284,76.6225,9.7825,76.6765]` (south, west, north, east). A later attempt to
download a wider context buffer and full road-member node tags failed; details
are in `data/raw/osm_fetch_failures.json`. The original response and its original
query (`osm_snapshot_query.overpassql`) are retained. The refresh request
(`osm_query.overpassql`) is separate and has not been misrepresented as the
successful snapshot's query. Original request-completion time was not captured;
metadata distinguishes archival verification time from OSM's dataset timestamp.
Road-member nodes reconstructed only from way geometry do not have node tags in
this snapshot unless separately returned by the query. Their attributes are
unknown, not absent; corresponding deficiency estimates remain assumption-based.

The default candidate radius is 3,000 m great-circle distance from the mapped
campus center. Selection is deterministic, targets at most 28 candidates, and
keeps fewer if the evidence supports fewer. Candidates include internal campus
roads as well as nearby public-road context; road ownership and public access
have not been verified.

1. Read mapped motor-road ways: motorway/trunk/primary/secondary/tertiary,
   unclassified, residential, living street and service, including `_link` forms.
   Motorway inclusion is not an assertion that an at-grade crossing is legal or
   feasible; such a feature would require separate screening.
2. Reconstruct adjacent road-node connectivity. A node with at least three
   distinct adjacent road nodes is a junction candidate, not necessarily a
   pedestrian crossing. Shared OSM node topology is used, not intersecting lines
   that might be grade-separated.
3. Include explicitly mapped road crossing nodes, still unverified in the field.
4. Also permit the nearest motor-road node within 100 m of a mapped destination
   as a hypothetical access candidate. Proximity does not establish a connected
   access route or legitimate crossing desire line.
5. Order mapped crossings first, junctions second, destination-access candidates
   third; within each group sort by distance to campus, then OSM ID. Greedily
   require at least 80 m between selected coordinates and stop at the target.

This favors mapped, near-campus junctions. It is not a complete or representative
crossing sample. `candidate_basis` records the reason; `location_status` always
states `hypothetical_candidate_not_verified_crossing`. IDs use `SYN-OSM-...` and
`CAND-OSM-...`. Names identify mapped roads and explicitly say hypothetical.
`feasibility_status=eligible` means **included in this simulation only**;
`engineering_feasibility=unknown_not_screened` prevents interpreting it as approval.
No invented field survey date is supplied: `survey_date=not_field_survey` and
`evidence_photo_ids=NO_FIELD_PHOTOS` are explicit sentinels.

## Geographic indicators

Destination points use node coordinates, Overpass centers where available, or the
arithmetic mean of an area's geometry vertices. The latter is an approximate
location, not an entrance or an area-weighted centroid. Same-named mapped objects
within 100 m are deduplicated; unnamed duplicates and differently named aliases
can remain. Feature centers, map incompleteness and query boundaries affect
proximity estimates.

`full_500m_query_buffer` flags whether the candidate's entire catchment lies inside
the actual snapshot bounds. A candidate near the extraction boundary can have
truncated amenity context. Such demand and destination estimates are marked very
low confidence with wider intervals; even a full query buffer does not establish
that OSM itself is complete.

Search destinations within **500 m straight-line distance**, not an audited
walk-network catchment. Destination weights `a` are provisional modelling choices:

| Mapped type | Weight a |
|---|---:|
| Hospital, clinic, school, kindergarten | 3.0 |
| College, university, pharmacy, bus station, marketplace | 2.5 |
| Bus stop or public-transport platform/stop position | 2.0 |
| Bank, post office, community centre, place of worship | 1.5 |
| Other shop, restaurant, cafe | 1.0 |

For each included destination at distance `d`, its contribution is `a*(1-d/600)`.
`I` is the sum of contributions; `M` is their maximum, or zero if none are mapped.
`B` is 1 when a mapped bus stop/platform/stop position lies within 250 m, otherwise
0. No nearby mapped destination means mapping evidence is sparse; it does **not**
prove no destination or demand exists. Destination object references, indicator
counts and intensities are retained per row.

## Deterministic 1–5 central scoring

All five scores increase intervention priority. `round_clip(x)` means
`min(5,max(1,floor(x+0.5)))`. These ordinal categories are not calibrated rates;
TOPSIS treats their spacing as equal as an explicit approximation.

Generation seed is **20261024**. Each candidate gets its own Python
`random.Random(f"{seed}:{osm_node_id}")` stream. The order of draws in
`scripts/build_synthetic_dataset.py` is part of the reproducible specification.
Never tune the seed to obtain a preferred rank.

### 1. Vehicle exposure (`vehicle_exposure` / `vehicle_mid`)

Use the highest-hierarchy adjacent mapped road; break ties by lower way ID.
Base values: motorway/trunk/primary 5; secondary 4; tertiary 3;
unclassified/residential 2; living street/service 1. Add 0.5 for an explicitly
numeric mapped `lanes >= 3`, and 0.5 for an explicitly numeric mapped
`maxspeed >= 60`. Unknown or nonnumeric tags make no adjustment. Add uniform
variation `U(-0.35,0.35)` and round/clip. At ordinary integer bases that small
variation will not itself change the category. **A mapped speed-limit tag is not
a measured operating speed; road class is not a measured traffic volume.**

### 2. Pedestrian demand (`pedestrian_demand` / `ped_mid`)

`round_clip(1 + 1.05*ln(1+I) + 0.35*B + 0.12*(vehicle_score-2) + U(-0.65,0.65))`.
This combines mapped destination intensity, bus proximity, a mild assumed
association with the road context, and seeded synthetic variation. It does not
invent pedestrians/hour, peak-hour counts or survey windows.

### 3. Essential destination access (`essential_destination_access` / `destination_mid`)

`round_clip(1 + 1.05*M + 0.25*ln(1+I))`. This emphasizes the strongest nearby mapped
essential destination, while demand emphasizes total intensity and bus proximity.
They are correlated by design but not identical formulas. This is a **synthetic
proximity-importance proxy**, not verified essential-destination access. It relaxes
the field model's walk-network evidence requirement for demonstration only; shared
amenity inputs can double count context. Inspect the correlation export and the
four-versus-five criterion comparison rather than assuming independence.

### 4. Accessibility deficiency (`accessibility_deficiency` / `access_mid`)

Start with neutral prior 3, add shared variation `U(-0.45,0.45)` and an independent
normal draw `N(0,0.85)`. Here and below this denotes mean 0 and **standard
deviation** 0.85, not variance 0.85. Apply only explicitly mapped candidate-node
evidence: wheelchair yes/designated −1.2, wheelchair no +1.2; lowered/flush kerb or
sloped_curb yes −0.8, raised kerb +0.8; tactile paving yes −0.4, explicit no +0.4.
Round/clip.
Missing tags leave the prior unchanged; they are **unknown, not absent**.
The prior and stochastic variation are modelling assumptions, not observations.

### 5. Control/visibility deficiency (`control_visibility_deficiency` / `deficiency_mid`)

Start with 3, the same shared variation, `0.2*(vehicle_score-3)` and a separate
normal draw `N(0,0.85)`. Explicitly mapped traffic signals at the candidate reduce
the value by 1.1; otherwise explicit zebra/marked crossing evidence (including
`crossing_ref=zebra`) reduces it by
0.7. Explicit lighting at the node, or on its selected road, reduces it by 0.4.
Round/clip. The exposure association is a synthetic complexity assumption, not
evidence of poor visibility. Lighting/markings/signals may be out of date and do
not verify operating condition, sight lines or compliance. Missing tags do not
increase deficiency. Unmapped attributes use a prior with clearly labelled low
confidence, not invented condition observations.

## Fuzzy ranges and confidence

The central scores are integers; their synthetic modelling bounds can be fractional:
`low=max(1,mid-width)`, `high=min(5,mid+width)`.
Width is 1.0 for low-confidence contextual/mapped proxies and 1.5 for very-low
confidence assumption-based deficiencies or destination estimates with no nearby
mapped destinations. Demand and destination estimates with a truncated or unknown
query buffer also use width 1.5. These labels express evidence quality, **not statistical
confidence levels**. Wider intervals are a heuristic stress-test representation,
not elicited membership functions, probability distributions or confidence
intervals. Clipping makes intervals asymmetric at the scale boundaries.

Store the five requested integer columns together with the existing pipeline's
`ped_*`, `vehicle_*`, `access_*`, `deficiency_*`, `destination_*` triples. The
synthetic validator requires centers to match the corresponding integer columns
and all bounds to lie in 1–5. The original field mode still requires counts and
0–3 audits; it is not silently reinterpreted as ordinal synthetic data.

## Execution, outputs and verification

See README for commands. Cached generation needs no network; fetching a newer
OSM snapshot is an explicit refresh and may change candidates and ranks.
`synthetic_generation_manifest.json` records snapshot, generator and CSV hashes,
seed, scope and candidate count. `pedestrian_crossings_observed.csv` is a
header-only template: **zero actual field observations are available**. It is not
populated with OSM proxies or synthetic scores.

The unchanged model normalizes shared criterion bounds, removes non-discriminating
criteria, renormalizes equal weights, sums Chen vertex distances, calculates
closeness, and orders by descending score with ID display ordering for exact ties.
Ranks are assigned before CSV display rounding. Near-equal floating-point scores
can have different ranks even when a viewer displays identical decimals; such
differences are not meaningful priority separation. For exact CSV round-trips in
pandas use `float_precision="round_trip"`.
`outputs/fuzzy_topsis_results.csv` uses **all five criteria** (the extension
model). The separately named base ranking, crisp baseline, calculation trace,
weight sensitivity and uncertainty-width diagnostics retain the original
**four-criterion baseline** definition. Their robustness statements do not
automatically apply to the five-criterion result. Equal weights remain provisional.

Tests verify raw-node/road linkage, coordinates, radius/spacing, unique IDs,
score types, interval bounds, provenance, absence of imputation, source-snapshot
reproducibility, all-five-criterion computation, and existing independent arithmetic
checks. Passing tests demonstrates implementation consistency, not empirical
accuracy or sound engineering decisions. Re-rankings caused by adding or removing
alternatives are possible because normalization is candidate-set dependent.

## Limitations and permitted claims

### Preserved snapshot summary (24 October 2026)

- 431 returned OSM elements yield 286 accepted motor-road ways and 91 mapped
  destination features after the limited name/proximity deduplication rule.
- 28 selected coordinates: 27 mapped-road-junction candidates and one
  explicitly mapped crossing, still not independently verified. No claim is made
  that these are 28 existing pedestrian crossings.
- All selected coordinates have their 500 m context disk inside the saved query
  rectangle; the completeness flag does not establish map completeness.
- The mapped crossing records `crossing_ref=zebra` and `tactile_paving=no`.
  These inform low-confidence proxies. The other 27 candidates have no
  recognized candidate-node accessibility or control evidence in this extract;
  their deficiency centers are explicitly assumption-based.
- Demand/destination central-score Spearman correlation is approximately 0.80,
  confirming substantial overlap of the constructed proxies, not independent
  validation. The five-criterion ranking can double count this context.
- The full CLI was run with 1,000 seeded weight draws. All 14 pipeline exports
  were byte-identical in a second run from the same input and environment.
  Verification checks and environment details are in `reports/synthetic_verification.json`.

### Interpretation

Permitted: “A reproducible simulation using public map context and explicit
synthetic assumptions demonstrates fuzzy TOPSIS for hypothetical candidate
improvements around IIIT Kottayam.”

Not permitted: “These are the most dangerous crossings,” “measured pedestrian
demand,” “verified accessible routes,” “expected crashes prevented,” or “approved
feasible engineering packages.” Obtain actual counts, independent audits, access
and route verification, costs and authority review before making operational
recommendations. The editable Word/PDF report is not automatically rewritten by
this dataset task and must not be assumed to describe this new experiment.
