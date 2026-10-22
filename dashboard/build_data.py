"""Build the dashboard's datasets from the research agents' stats.csv files.

Every output row keeps the stat_id, publisher, source_url and verification of the
row it came from, so each figure on the dashboard can be traced to its source.
Run: python3 -I dashboard/build_data.py  (from the repo root)
"""
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "dashboard", "data")

REGIONS = ["North East", "North West", "Yorkshire and The Humber", "East Midlands",
           "West Midlands", "East of England", "London", "South East", "South West",
           "Wales", "Scotland", "Northern Ireland"]

rows = {}
for theme in ["ise", "salaries", "outcomes", "apprenticeships", "vacancies", "gapfill"]:
    path = os.path.join(DATA, theme, "stats.csv")
    if not os.path.exists(path):
        continue
    for r in csv.DictReader(open(path, encoding="utf-8")):
        rows[r["stat_id"]] = r


VERIFICATION_LABELS = {
    "direct": "Read from source data",
    "search-official": "Official source, via search",
    "search-secondary": "Secondary source",
}


def fmt(v, unit):
    trim = lambda x: f"{x:.2f}".rstrip("0").rstrip(".")
    if unit == "GBP":
        return f"£{round(v):,}"
    if unit in ("percent", "percent_of_employers"):
        return f"{trim(v)}%"
    if unit == "pct_change":
        sign = "+" if v > 0 else "−" if v < 0 else ""
        return f"{sign}{trim(abs(v))}%"
    if unit == "index_feb2020_100":
        return f"{v:.1f}"
    if unit == "count":
        return f"{round(v):,}"
    return trim(v)


def cite(sid, **extra):
    r = rows[sid]
    value = float(r["value"])
    out = {"stat_id": sid, "value": value, "value_label": fmt(value, r["unit"]), "unit": r["unit"],
           "period": r["period"], "publisher": r["publisher"], "source_title": r["source_title"],
           "source_url": r["source_url"], "verification": r["verification"],
           "verification_label": VERIFICATION_LABELS.get(r["verification"], r["verification"])}
    out.update(extra)
    return out


def pick(pred):
    return [r for r in rows.values() if pred(r)]


def write(name, data):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{name}: {len(data)} rows")


# ---------------------------------------------------------------- map layers
LAYERS = [
    # id, title, short note, matcher
    ("grad_pay_15m", "Graduate pay, 15 months after graduating",
     "Average salary of 2022/23 graduates in full-time work, by region of work (no further study). Luminate analysis of HESA Graduate Outcomes.",
     lambda r: r["metric"] == "avg_salary_graduates_15m_by_region_of_work"
     and r["period"].startswith("2022/23") and r["breakdown_value"] == "No significant further study"),
    ("grad_pay_5y", "Graduate earnings, 5 years after graduating",
     "Median earnings in the 2023-24 tax year of first-degree graduates of English universities, by the region they now live in. DfE LEO. Graduates of Scottish, Welsh and NI universities are not included.",
     lambda r: r["metric"] in ("median_earnings_grads_5yag_by_region", "leo_median_earnings_5yag") and r["period"].startswith("2023-24")),
    ("job_postings", "Job postings vs pre-pandemic",
     "Indeed job postings index, all postings, 16 Oct 2026. 100 = 1 Feb 2020. Covers all jobs, not graduate jobs only.",
     lambda r: r["metric"] == "Indeed job postings index by region (latest)"),
    ("job_postings_yoy", "Job postings, change on a year earlier",
     "Change in the Indeed job postings index, 16 Oct 2025 to 16 Oct 2026. All postings.",
     lambda r: r["metric"] == "Indeed job postings by region, change on a year earlier"),
    ("appr_starts", "Apprenticeship starts, 2024/25",
     "England regions: DfE starts by academic year (rounded, via Commons Library). Scotland: Modern Apprenticeships. Wales: programmes started. NI: all programmes. Definitions differ by nation.",
     lambda r: r["metric"] == "apprenticeship_starts" and r["period"] == "2024/25"
     and r["region"] in REGIONS and (r["breakdown_value"] in ("", "Modern Apprenticeship", "All apprenticeships"))),
    ("home_retention", "Graduates working in their home region",
     "Share of 2023/24 UK-domiciled graduates in work who work in the region they lived in before university. HESA Graduate Outcomes. Only regions named in HESA's text are available.",
     lambda r: r["metric"] == "go_work_in_home_region_share" and r["period"] == "2023/24"),
    ("degree_share", "Working-age adults with a degree",
     "Share of people aged 16-64 qualified to RQF level 4 or above (degree or equivalent), January to December 2025. ONS Annual Population Survey via Nomis. Northern Ireland is not covered by Nomis profiles.",
     lambda r: r["metric"] == "pop_rqf4plus_share" and r["period"] == "Jan-Dec 2025"),
    ("entry_rate", "18-year-olds entering higher education",
     "UCAS 18-year-old entry rate, 2025 cycle.",
     lambda r: r["metric"] == "entry_rate_18yo" and r["theme"] == "gapfill" and r["period"].startswith("2025")),
]
map_rows = []
for lid, title, note, pred in LAYERS:
    found = {}
    for r in pick(lambda r: r["region"] in REGIONS and pred(r)):
        found.setdefault(r["region"], r)  # first row per region wins
    if len(found) < 5:
        print(f"skip layer {lid}: {len(found)} regions", file=sys.stderr)
        continue
    for reg, r in found.items():
        map_rows.append(cite(r["stat_id"], layer=lid, layer_title=title, layer_note=note, region=reg))
write("map_layers.json", map_rows)

# ------------------------------------------------- regional job postings, 2020-26
reg_trend = [cite(r["stat_id"], region=r["region"], year=int(r["period"]))
             for r in pick(lambda r: r["metric"] == "Indeed job postings index by region (annual average)")]
reg_trend.sort(key=lambda x: (x["region"], x["year"]))
write("regional_postings.json", reg_trend)

# ------------------------------------------------------------ national series
SERIES = [
    ("apps_per_vacancy", "Applications per graduate vacancy (ISE)",
     ["ise_077", "ise_078", "ise_079", "ise_080", "ise_081", "ise_013", "ise_067"]),
    ("grad_hiring_change", "Graduate hiring change on a year earlier (ISE)",
     ["ise_089", "ise_090", "ise_091", "ise_092", "ise_093", "ise_094", "ise_095"]),
    ("grad_pay_median", "Median graduate salary 15 months after graduating (HESA)",
     ["SAL-001", "SAL-002", "SAL-003", "SAL-004", "SAL-005"]),
    ("ft_employment", "Graduates in full-time work 15 months on (HESA)",
     ["outc_001", "outc_002", "outc_003", "outc_004", "outc_005", "outc_006", "outc_007"]),
    ("appr_starts_england", "Apprenticeship starts in England (DfE)",
     ["APP-024", "APP-025", "APP-026", "APP-027", "APP-028", "APP-029", "APP-033", "APP-034",
      "APP-035", "APP-036", "APP-037", "APP-038", "APP-001"]),
    ("emp_rate_graduates", "Employment rate, graduates (DfE, England)",
     ["outc_146", "outc_145", "outc_134", "outc_133", "outc_123", "outc_106"]),
    ("emp_rate_nongraduates", "Employment rate, non-graduates (DfE, England)",
     ["outc_148", "outc_147", "outc_141", "outc_135", "outc_127", "outc_108"]),
]
nat = []
for sid_series, title, ids in SERIES:
    for i, sid in enumerate(ids):
        r = rows[sid]
        label = r["period"].split(" ")[0]
        nat.append(cite(sid, series=sid_series, series_title=title, label=label, order=i))
write("national_series.json", nat)

# ------------------------------------------------------------ subject pay
subj = [cite(r["stat_id"], subject=r["breakdown_value"])
        for r in pick(lambda r: r["metric"] == "median_salary_graduates_15m" and r["period"].startswith("2023/24")
                      and r["breakdown_dim"] == "subject" and "(all)" not in r["breakdown_value"])]
if not subj:  # fall back to explicit ids if the breakdown_dim label differs
    subj = [cite(f"SAL-0{n}", subject=rows[f"SAL-0{n}"]["breakdown_value"]) for n in range(12, 24)]
write("subject_pay.json", subj)

# ----------------------------------------------- occupations (Indeed, graduate-entry)
OCC = ["Media & Communications", "Marketing", "Data & Analytics", "IT Systems & Solutions", "Software Development",
       "Human Resources", "Accounting", "Scientific Research & Development", "Project Management", "Management",
       "Banking & Finance", "Insurance", "Legal", "Architecture", "Social Science", "Education & Instruction",
       "Electrical Engineering", "Mechanical Engineering", "Civil Engineering"]
occ = [cite(r["stat_id"], occupation=r["breakdown_value"])
       for r in pick(lambda r: r["metric"] == "Indeed job postings index by occupational sector (latest)"
                     and r["breakdown_value"] in OCC)]
write("occupation_postings.json", occ)

# ------------------------------------------------------------ ISE top 10
TOP10 = [
    (1, "Graduate hiring fell, apprentice hiring rose", "−8%", "ise_001",
     "School and college leaver hiring rose 8%; the entry-level market overall fell 5%.",
     "2025/26: graduate hiring recovered 4%, but 0.8% excluding a few large employers."),
    (2, "Graduates hired per apprentice", "1.8", "ise_004",
     "Down from 2.3 in 2024. Employers forecast 1.6.", ""),
    (3, "Median graduate starting salary", "£33,000", "ise_007",
     "School and college leavers: £24,000. Graduate pay fell 1% in real terms.", ""),
    (4, "Applications per graduate vacancy", "140", "ise_013",
     "The highest since ISE began collecting data in 1991. Retail, FMCG and tourism: 290 per role.",
     "2025/26: 141 applications per vacancy."),
    (5, "Employers worried AI misrepresents graduates", "48%", "ise_014",
     "52% for school and college leavers. Employers frequently seeing cheating rose from 7% to 15%.",
     "2026: 67% for graduates."),
    (6, "Employers redesigning or reviewing recruitment for AI", "79%", "ise_018",
     "About a third are redesigning; 46% are reviewing.", ""),
    (7, "Employers committed to equality, diversity and inclusion", "92%", "ise_020",
     "66% report no change in their commitment.", ""),
    (8, "Agree former interns are more work-ready", "77%", "ise_022",
     "ISE Student Development Survey 2025, 148 employers.", ""),
    (9, "Find graduates below expectations on self-awareness", "54%", "ise_023",
     "Up from 43% in 2024 and 35% in 2023. 46% raise concerns about resilience.", ""),
    (10, "Graduate pay growth over the first three years", "+37%", "ise_027",
     "School and college leavers: +39% (averages). Position in the list not confirmed.", ""),
]
write("ise_top10.json", [cite(sid, rank=rk, headline=h, display=disp, detail=d, update_2026=u)
                         for rk, h, disp, sid, d, u in TOP10])

# ------------------------------------------------------------ key figures
KEY = [
    ("adzuna_grad", "Graduate job adverts (Adzuna)", "8,383", "vac_0788", "July 2026, the lowest since tracking began in 2016"),
    ("adzuna_grad_yoy", "Graduate adverts, change on a year earlier (Adzuna)", "−45.6%", "vac_0789", "July 2026"),
    ("indeed_grad_yoy", "Indeed postings with ‘graduate’ in the title", "−7%", "vac_0762", "Change on a year earlier, 10 Jul 2026"),
    ("highfliers_cum", "Graduate recruitment at top 100 employers", "−24.5%", "vac_0817", "Cumulative change, 2022 to 2025 (High Fliers)"),
    ("hesa_pay", "Median graduate salary, 15 months on", "£30,000", "SAL-005", "2023/24 graduates, HESA"),
    ("ise_forecast", "Graduate hiring forecast, 2026/27", "+7%", "ise_065", "ISE employers' forecast"),
    ("appr_starts", "Apprenticeship starts in England", "353,500", "APP-001", "2024/25, DfE"),
    ("appr_degree", "Degree-level apprenticeship starts", "60,350", "APP-012", "Levels 6 and 7, England 2024/25, up 20%"),
]
write("key_figures.json", [cite(sid, id=k, label=l, display=disp, detail=d) for k, l, disp, sid, d in KEY])
