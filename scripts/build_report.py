"""Build the academic report from reproducible hypothetical exports.

Optional authoring dependency: python-docx. Runtime analysis needs only
requirements.txt. Run the demo before rebuilding this report.
"""
from pathlib import Path
import csv
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
doc = Document()
section = doc.sections[0]
section.page_width, section.page_height = Inches(8.27), Inches(11.69)
section.top_margin = section.bottom_margin = Inches(.7)
section.left_margin = section.right_margin = Inches(.75)
style = doc.styles['Normal']
style.font.name = 'Times New Roman'
style.font.size = Pt(11)
style.paragraph_format.space_after = Pt(7)
style.paragraph_format.line_spacing = 1.08
for name in ['Title', 'Heading 1', 'Heading 2']:
    doc.styles[name].font.name = 'Times New Roman'
    doc.styles[name].font.color.rgb = RGBColor(0, 0, 0)
doc.styles['Title'].font.size = Pt(19)
doc.styles['Heading 1'].font.size = Pt(14)
doc.styles['Heading 2'].font.size = Pt(12)
for named_style in doc.styles:
    for border in list(named_style.element.iter(qn('w:pBdr'))):
        border.getparent().remove(border)
    for fonts in named_style.element.iter(qn('w:rFonts')):
        for attribute in list(fonts.attrib):
            if attribute.endswith('Theme'):
                del fonts.attrib[attribute]

def p(text):
    doc.add_paragraph(text)

def h(text):
    doc.add_heading(text, level=1)

def table(headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Light Shading Accent 1'
    for cell, text in zip(t.rows[0].cells, headers):
        cell.text = text
    repeat = OxmlElement('w:tblHeader')
    t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row in rows:
        for cell, value in zip(t.add_row().cells, row):
            cell.text = str(value)
    for row in t.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(4)
                for run in paragraph.runs:
                    run.font.size = Pt(10)
    return t

def read(name):
    with (ROOT / 'results' / ('hypothetical_' + name + '.csv')).open() as f:
        return list(csv.DictReader(f))

doc.add_paragraph('A Fuzzy TOPSIS Framework for Prioritising Pedestrian Crossing Safety and Accessibility Improvements', 'Title')
p('Soft Computing Assignment P20 • IIIT Kottayam')
h('Abstract')
p('This project develops a reproducible decision-support procedure for prioritising feasible pedestrian-crossing improvement packages. Four baseline criteria describe pedestrian demand, vehicle exposure, accessibility deficiency and control or visibility deficiency. Triangular fuzzy numbers express documented observation ranges or assessor disagreement. A declared adaptation of triangular fuzzy TOPSIS combines observed-range normalisation, provisional equal weights and summed vertex distances. An extension adds essential-destination access importance. Four hypothetical alternatives demonstrate the complete pipeline; no site survey or empirical priority list is claimed. Evaluation compares a crisp baseline, the extension, 1,000 weight perturbations and three uncertainty-width scenarios. The example shows that a stable leading candidate under some assumptions can coexist with substantial changes elsewhere in the ranking. Collection forms, calculation traces, tests and source records support subsequent field application. Independent validation and engineering review remain necessary before a real allocation decision.')
p('Keywords: pedestrian crossings; accessibility; triangular fuzzy numbers; TOPSIS; sensitivity analysis')
h('1 Introduction and decision scope')
p('A crossing improvement decision combines evidence measured in different units and observations that vary across time or assessors. A transparent ranking can help reviewers identify packages requiring attention, provided the score is interpreted within its candidate set. The decision here is which feasible package should receive earlier review. It is neither an estimate of accident probability nor a calculation of treatment effectiveness. A package may combine related actions at one crossing; choosing among multiple competing designs at the same site requires a separate engineering assessment.')
p('The proposed study boundary covers the IIIT Kottayam campus and immediately adjoining public-road approaches. This is a study design: the crossing inventory and boundary have not been verified on site. Candidate records must identify a crossing, describe its proposed intervention, cite photographs and state feasibility. Only one eligible package per crossing enters the comparison. Rejected candidates retain a written reason. The campus facilities team and relevant road authority are the intended reviewers; the algorithm cannot grant approval or establish compliance.')
h('2 Research question and contribution')
p('The research question is whether adding essential-destination access changes the ordering or top group after local demand and deficiency criteria have been held fixed. The contribution is an inspectable implementation and an explicit comparison protocol. Applying TOPSIS at a new location alone is not a novelty claim. A changed ranking demonstrates that the additional criterion matters mathematically; it does not establish that the revised recommendation is better. That judgement needs evidence independent of the inputs.')

doc.add_page_break()
h('3 Related work and evidence sources')
p('Structured inspection is a relevant precedent, but the decision target and geographical setting matter. Table 1 distinguishes crossing assessment, pedestrian satisfaction and behavioural modelling. The detailed source register records verified bibliographic metadata, access dates and reuse conditions. Claims from abstracts are kept at abstract level; inaccessible details have not been reconstructed.')
p('Table 1. Literature comparison and transfer limits')
table(['Study', 'Question and method', 'Project implication'], [
    ['Battistini et al. [1]', 'Checklist-based decision support at ten unsignalized crossings on two Bologna roads.', 'Supports systematic site inspection; Italian scores are not local compliance thresholds.'],
    ['Majumdar et al. [2]', 'Pedestrian satisfaction and TOPSIS prioritisation of sidewalk and crosswalk attributes.', 'Supports pedestrian-focused criteria; ranking attributes differs from ranking site packages.'],
    ['Alver and Katanalp [3]', 'Integrated AHP and fuzzy logic for gap acceptance at semicontrolled crossings.', 'Shows a transport application of fuzzy modelling; does not validate these ratings.'],
    ['Chen [4]; Jefmański and Sagan [5]', 'Triangular fuzzy TOPSIS foundation and analysis of fuzzy scale choices.', 'Motivates vertex distances and explicit sensitivity to representation choices.']])
p('The three transport studies address related decisions rather than providing local measurements. Chen [4] supplies the method lineage; this project does not claim an unchanged implementation of its group linguistic formulation. The full original paper was not accessible through the earlier open-source review. The declared project equations below therefore define the implemented model precisely. The open exposition in [5] also supports examining sensitivity to fuzzy conversion choices.')
h('4 Criteria and data collection')
p('All criteria increase priority. Table 2 defines the small baseline and its extension. Equal weights are a transparent starting point because no expert elicitation has occurred. Cost is excluded because no verified estimates exist. Feasibility is an inclusion gate, not an invented numerical benefit.')
table(['Code', 'Criterion and unit', 'Evidence and uncertainty'], [
    ['P1', 'Pedestrian demand, persons/hour', 'Repeated matched windows; minimum, median, maximum rates.'],
    ['P2', 'Vehicle exposure, vehicles/hour', 'Same windows and approach; minimum, median, maximum rates.'],
    ['P3', 'Accessibility deficiency, 0–3', 'Independent photo-supported audits; documented rating range.'],
    ['P4', 'Control or visibility deficiency, 0–3', 'Structured checklist; keep components distinct from P3.'],
    ['E1', 'Essential-destination access, 0–3', 'Verified routes, destination IDs and alternative-route evidence.']])
p('The protocol proposes two ordinary weekdays, morning, midday and evening periods, and three 15-minute intervals per period. Counts become hourly rates using count × 60/minutes. Weather and disruptions are recorded; atypical sessions are repeated or analysed separately. Two assessors retain independent ratings and evidence IDs. Disagreement is preserved or adjudicated with a written reason. OpenStreetMap is a potential inventory aid [6], not a verified local dataset in this submission. No map extract, traffic counts or field photographs are included.')

doc.add_page_break()
h('5 Mathematical specification')
p('For alternative i and criterion j, x̃ᵢⱼ = (lᵢⱼ, cᵢⱼ, uᵢⱼ), with l ≤ c ≤ u. For counts, the three values are the minimum, median and maximum observed hourly rates. For audits, they record the lower, central and upper documented ratings. The triangular shape is a modelling approximation: observed bounds alone do not establish that membership declines linearly. Temporal variation and assessor disagreement are different sources of imprecision and must remain identifiable in the underlying records.')
p('For a nondegenerate triangle (l,c,u), membership is zero outside [l,u], rises as (x−l)/(c−l) from l to c, equals one at c, and falls as (u−x)/(u−c) from c to u. A hypothetical triangle (100,120,160) has membership 0.5 at 110 and 140 and membership 1 at 120. These grades are not probabilities. When l=c or c=u, the corresponding rising or falling segment is absent; a fully crisp triple concentrates at its one value.')
p('Shared outer bounds are Lⱼ = minᵢ lᵢⱼ and Uⱼ = maxᵢ uᵢⱼ. Each component q is normalised by zᵢⱼq = (xᵢⱼq−Lⱼ)/(Uⱼ−Lⱼ). Identical criterion triples across alternatives are excluded, including zero-range criteria. The remaining weights are renormalised. This avoids division by zero and prevents a non-discriminating criterion changing the score. All included criteria are priority-oriented, so no cost reversal is applied.')
p('With m active criteria, wⱼ = 1/m initially. Form the weighted triangle ṽᵢⱼ = wⱼz̃ᵢⱼ. The positive ideal is Aⱼ⁺ = (wⱼ,wⱼ,wⱼ), and the negative ideal is Aⱼ⁻ = (0,0,0). These are theoretical corners of the weighted scale; they need not be observed packages. The normalisation, crisp weights and weighted ideals are explicit project adaptations, while the vertex metric and distance summation retain the Chen-style structure.')
p('d(ã,b̃) = √[((aₗ−bₗ)² + (a꜀−b꜀)² + (aᵤ−bᵤ)²)/3]')
p('Dᵢ⁺ = Σⱼ d(ṽᵢⱼ,Aⱼ⁺);     Dᵢ⁻ = Σⱼ d(ṽᵢⱼ,Aⱼ⁻);     Cᵢ = Dᵢ⁻/(Dᵢ⁺+Dᵢ⁻).')
p('Rank Cᵢ in descending order. Larger scores mean closer to the high-priority ideal relative to the low-priority ideal. A zero denominator is rejected. Exact equal scores receive the same minimum rank; alternative IDs determine display order. The program exports each normalised triple, active weight and criterion distance, so every total can be reconstructed. Appendix A independently checks a two-criterion example.')
h('6 Processing workflow and comparison design')
p('Figure 1. Reproducible workflow')
table(['Stage', 'Output'], [
    ['Inventory and evidence → feasibility gate', 'Eligible packages and retained rejection reasons'],
    ['Validate → derive triples → normalise', 'Clean matrix and preprocessing log'],
    ['Weight → calculate distances → rank', 'Scores and criterion calculation trace'],
    ['Compare → perturb assumptions → human review', 'Evaluation tables, chart and review priorities']])
p('The crisp comparator min–max scales central observations separately and averages active columns. The extension adds E1 at weight 1/5 and assigns each original criterion 1/5, preserving their relative weights. It asks about the effect of adding access importance; it is not a controlled test of predictive accuracy. Correlations among central criteria flag possible overlap, but four invented rows cannot establish independence or justify deleting a criterion.')

doc.add_page_break()
h('7 Implementation and hypothetical evaluation')
p('The Python pipeline validates required metadata, unique identifiers, ordered finite nonnegative triples, survey-date format and the 0–3 audit limits. It rejects missing measurements instead of replacing them with zero. Eight automated tests cover independent arithmetic, constant criteria, orientation, invalid data, duplicate identifiers, large weights and the evaluation exports. The run manifest records the input SHA-256 hash, runtime versions, seed and experiment settings. Input provenance and photograph authenticity still require human review.')
p('Table 3. Synthetic demonstration only; no actual crossing observations')
base = read('base_ranking')
ext = {r['alternative_id']: r for r in read('extension_ranking')}
crisp = {r['alternative_id']: r for r in read('crisp_baseline')}
table(['Alternative', 'Base score', 'Base rank', 'Crisp rank', 'Extended rank'], [
    [r['alternative_id'], f"{float(r['score']):.6f}", r['rank'], crisp[r['alternative_id']]['rank'], ext[r['alternative_id']]['rank']] for r in base])
p('HYP-A leads the four-criterion fuzzy model. HYP-B and HYP-D differ by only about 0.00146, which is too small to treat as a substantive field conclusion even if the inputs were observed. HYP-C moves from fourth to first when destination access is introduced. This reversal illustrates the question being tested: local deficiency and demand can yield a different ordering from a model that also values access consequences. No improvement in safety or decision quality follows from this numerical change alone.')
p('Table 4. Comparison of rankings on the same hypothetical alternatives')
table(['Comparison', 'Top choice changes', 'Top-three overlap', 'Spearman'], [
    [r['comparison'].replace('_', ' '), r['top1_changed'], f"{float(r['top_k_overlap']):.3f}", f"{float(r['spearman']):.3f}"] for r in read('comparisons')])
p('Spearman is correlation between average ranks and describes ordering agreement. Top-three overlap is the shared number of selected alternatives divided by three. Exact ties use ID order for selection statistics; this arbitrary boundary choice must be checked when ties occur. Neither agreement nor disagreement validates the ranking against a real outcome. The crisp comparison changes both fuzzy representation and scaling, so it cannot isolate the effect of uncertainty alone.')
h('8 Sensitivity to weights and uncertainty')
p('Weight sensitivity uses 1,000 reproducible draws with seed 20261009. Each equal weight is multiplied by an independent uniform factor between 0.8 and 1.2, then the vector is renormalised. These bounds are an exploratory scenario, not an elicited distribution of stakeholder preferences. HYP-A leads 864 draws (86.4%) and HYP-B leads 136 (13.6%). Thus even the leading base candidate is conditional on the chosen weighting assumptions. The saved SVG visualises these frequencies.')
p('Uncertainty sensitivity contracts each triangle around its central value using x̃(α) = c + α(x̃−c), for α = 0, 0.5 and 1, then recomputes the shared normalisation bounds. HYP-A remains first in these three scenarios. At α=0, B and C tie for second; at α=0.5, C is third and D fourth; at α=1, D is third. Rank correlations with the full-width model are approximately 0.632, 0.800 and 1.000. These are stress tests of the representation and its scaling, not improved measurements or calibrated uncertainty estimates.')

doc.add_page_break()
h('9 Interpretation and independent validation plan')
p('The calculation trace explains why a package receives its score: each criterion contributes a distance to the two ideals, and the summed distances determine closeness. A reviewer can inspect a high score alongside the original count intervals and audit photographs. The trace is more defensible than treating a final ranking as self-explanatory. In practice, close alternatives should be discussed together and checked for measurement differences that could reverse their order.')
p('Independent validation remains pending data collection. A reviewer who did not provide the original ratings should examine a preregistered sample of crossing records or sites without seeing model ranks. The validation form records accessibility barriers, control and visibility concerns, proposed action suitability and a written assessment of urgency. Preserve disagreements rather than adjusting inputs to match the model. Report the sample selection rule, reviewer role, evidence dates, agreement and unresolved differences. Expert agreement would support practical relevance, but would still not prove a reduction in crashes.')
p('The destination extension requires a verified destination inventory, walking routes and a defined catchment. Assess whether a crossing is a necessary link and whether a usable alternative route exists. An ordinary destination count can duplicate pedestrian demand and should not automatically become E1. The exported pairwise central-value correlations provide an initial overlap screen. A larger field sample and substantive route inspection are needed to decide whether the extension adds a distinct decision dimension.')
h('10 Limitations and remaining fieldwork')
p('There is no empirical ranking in this submission. The four HYP alternatives are invented solely for reproducibility and demonstration. Site identity, feasibility, observations, photo evidence and destination access have not been verified. The 0–3 audit rubric is a proposed study scale, not an Indian compliance standard. The exact instructor handout and individual author details were not supplied, so institutional formatting and contribution declarations require student review before submission.')
p('Min–max bounds depend on the candidate set; adding or removing a crossing can change scores and ordering. Triangular ranges combine observed variability with a shape assumption and do not encode a probability distribution. Equal weights and the perturbation interval express provisional choices. Uncertainty contraction also changes normalisation, so its effects should not be attributed solely to fuzziness. A small top-group overlap metric can conceal a major first-place reversal; multiple evaluation summaries are therefore reported.')
p('A priority order is not a budget-optimal portfolio. Real decisions need cost estimates, implementation dependencies, jurisdiction, accessibility requirements and engineering feasibility. Intervention effects and crash reduction would need a different evaluation design. The method must not be used to claim that a low-ranked crossing is safe, or that a high-ranked package has a quantified benefit. It supports a review process within a verified candidate set.')
h('11 Conclusion')
p('The project delivers a complete executable demonstration of a declared triangular fuzzy TOPSIS adaptation, a transparent crisp comparator and an essential-destination extension. The example demonstrates why assumption checks matter: weight variation changes the leading candidate in some draws, uncertainty contraction changes lower ranks, and the extension changes the winner. The implementation exposes intermediate calculations and rejects incomplete inputs. The remaining empirical contribution is to collect and verify the crossing evidence, run the same pipeline and obtain independent review. Until then, the defensible result is methodological reproducibility, not a recommendation for a real crossing.')

doc.add_page_break()
h('References')
with (ROOT / 'docs/source_register.csv').open() as f:
    sources = {r['id']: r for r in csv.DictReader(f)}
for index, key in enumerate(['S2', 'S3', 'S4', 'S1', 'S8', 'S7'], 1):
    r = sources[key]
    p(f"[{index}] {r['full_reference']} {r['url']}")
h('Appendix A Independent arithmetic example')
p('Use two already normalised criteria with weights 0.4 and 0.6. Alternative A has triangles (0.2,0.4,0.6) and (0.5,0.7,0.9); alternative B has (0.7,0.8,0.9) and (0.1,0.2,0.3). For A, the weighted triangles are (0.08,0.16,0.24) and (0.30,0.42,0.54). The positive ideals are (0.4,0.4,0.4) and (0.6,0.6,0.6); both negative ideals are zero.')
table(['Quantity for A', 'Criterion 1', 'Criterion 2', 'Sum'], [
    ['Distance to positive', '0.2487301081', '0.2049390153', '0.4536691234'],
    ['Distance to negative', '0.1728197520', '0.4312771731', '0.6040969250']])
p('For example, the first positive distance is √[(0.32²+0.24²+0.16²)/3] = 0.2487301081. Thus C_A = 0.6040969250 / (0.4536691234+0.6040969250) = 0.5711063670. The automated check compares these independently calculated constants to the implementation. The demonstration calculation trace extends this audit trail to every baseline alternative and criterion.')
h('Appendix B Reproduction and field handoff')
p('Install requirements.txt in a Python 3.10+ environment. Run python src/run_project.py --demo and python -m unittest discover -s tests -v. For real data, complete a copy of data/raw_observation_template.csv and retain the count and audit forms. Run python src/run_project.py --input data/my_completed_observations.csv --output-dir results/field_run. Keep hypothetical and field outputs separate. The field prefix identifies the input mode, not independently certified data.')
p('README.md documents all exports. docs/field_readiness.md lists evidence needed before field interpretation; docs/viva_guide.md explains the main modelling choices. The author should complete docs/contribution_log.csv with actual work history. Report regeneration additionally requires python-docx and uses scripts/build_report.py after regenerating the demo.')

footer = section.footer.paragraphs[0]
footer.alignment = 2
field = OxmlElement('w:fldSimple')
field.set(qn('w:instr'), 'PAGE')
footer._p.append(field)
doc.core_properties.title = 'Fuzzy TOPSIS Pedestrian Crossing Prioritisation'
doc.core_properties.author = ''
doc.save(ROOT / 'P20_Fuzzy_TOPSIS_Report.docx')
