"""Write the short project report (outputs/report.pdf) from the result tables and figures."""
import os

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (Image, KeepTogether, ListFlowable, ListItem, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = os.path.dirname(os.path.abspath(__file__))
TABLES, FIGURES = os.path.join(ROOT, "outputs", "tables"), os.path.join(ROOT, "outputs", "figures")
OUT = os.path.join(ROOT, "outputs", "report.pdf")
REPO = "github.com/anayaanj/predicting-airbnb-bookings"

INK, MUTED, RULE, PANEL = colors.HexColor("#14181F"), colors.HexColor("#5B6472"), colors.HexColor("#D9DDE3"), colors.HexColor("#F3F5F8")
LONDON, PARIS = colors.HexColor("#2A78D6"), colors.HexColor("#C2501F")
WIDTH = A4[0] - 40 * mm

S = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=INK, spaceAfter=4),
    "sub": ParagraphStyle("sub", fontName="Helvetica", fontSize=10, leading=14, textColor=MUTED, spaceAfter=14),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=INK, spaceBefore=12, spaceAfter=6, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=INK, spaceBefore=8, spaceAfter=4, keepWithNext=1),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=INK, alignment=TA_LEFT, spaceAfter=6),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8, leading=11, textColor=MUTED),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=8.5, leading=11, textColor=INK),
}


def table(name, city=None):
    return pd.read_csv(os.path.join(TABLES, f"{city + '_' if city else ''}{name}.csv"), index_col=0)


def p(text, style="body"):
    return Paragraph(text, S[style])


def bullets(items):
    return ListFlowable([ListItem(p(t), leftIndent=10) for t in items], bulletType="bullet", start="•", leftIndent=12, bulletFontSize=8)


def figure(name, caption, scale=1.0):
    path = os.path.join(FIGURES, name)
    w, h = ImageReader(path).getSize()
    return KeepTogether([Image(path, width=WIDTH * scale, height=WIDTH * scale * h / w), p(caption, "small"), Spacer(1, 8)])


def grid(rows, widths, header=True):
    t = Table([[Paragraph(str(c), S["cell"]) for c in r] for r in rows], colWidths=widths, hAlign="LEFT")
    style = [("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), PANEL), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    t.setStyle(TableStyle(style))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, 12 * mm, f"BU7154 · Airbnb bookings in London and Paris · {REPO}")
    canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, str(doc.page))
    canvas.restoreState()


# Numbers used in the text, all read from the analysis tables
pct, x = "{:.1%}".format, lambda v: f"{v:.2f}×"
CITIES = ["London", "Paris"]
log = {c: pd.read_csv(os.path.join(ROOT, "data", c, f"{c}_data_log.csv"), header=None, index_col=0)[1] for c in CITIES}
fit = {c: table("count_fit", c) for c in CITIES}
mfit = {c: table("model_fit", c) for c in CITIES}
A = {c: table("model_a", c) for c in CITIES}
ltm = {c: table("model_ltm", c) for c in CITIES}
stay = {c: table("long_stay", c) for c in CITIES}
A_stay = {c: table("model_long_stay", c) for c in CITIES}
scen = {c: table("scenarios", c) for c in CITIES}
lang = {c: table("language_share", c)["share"] for c in CITIES}
card = table("scorecard")
pooled = table("pooled_interactions")
trans = table("translation_check", "Paris")
price = {c: table("price_missing", c) for c in CITIES}
held = {c: card[c].str.startswith("✅").sum() for c in CITIES}
tested = {c: (~card[c].str.startswith("⚠")).sum() for c in CITIES}
zero = {c: fit[c].loc["0", "Observed"] for c in CITIES}
lift = {c: scen[c].loc["Everybody is a superhost", "Expected reviews"] / scen[c].loc["As observed", "Expected reviews"] - 1 for c in CITIES}

story = [
    p("What gets an Airbnb listing booked?", "title"),
    p("Count models of guest reviews in London and Paris · BU7154 Foundations of Business Analytics · "
      f"InsideAirbnb snapshots of {log['London']['Snapshot date (InsideAirbnb)']} (London) and "
      f"{log['Paris']['Snapshot date (InsideAirbnb)']} (Paris)", "sub"),
    p("Key findings", "h1"),
    bullets([
        f"<b>{pct(zero['London'])}</b> of London and <b>{pct(zero['Paris'])}</b> of Paris listings have never been reviewed.",
        f"<b>Superhost status</b> is the strongest predictor: {x(A['London'].loc['superhost', 'IRR'])} expected reviews in London and "
        f"{x(A['Paris'].loc['superhost', 'IRR'])} in Paris. More amenities ({x(A['London'].loc['n_amenities_z', 'IRR'])} / "
        f"{x(A['Paris'].loc['n_amenities_z', 'IRR'])} per SD) also help; a missing price marks a closed listing.",
        "Review counts are heavily overdispersed, so a <b>Negative Binomial</b> model fits far better than Poisson.",
        f"Host tenure reflects listing age: its effect reverses on reviews from the last 12 months "
        f"({x(ltm['London'].loc['host_years_z', 'IRR'])} London, {x(ltm['Paris'].loc['host_years_z', 'IRR'])} Paris).",
        f"<b>{held['London']} of {tested['London']}</b> testable findings from Biswas et al. (2020) and Sengupta et al. (2021) hold in "
        f"London and <b>{held['Paris']} of {tested['Paris']}</b> in Paris. The overall rating goes the opposite way in both.",
    ]),

    p("1. Question and data", "h1"),
    p("Airbnb does not publish bookings, so the number of guest reviews is the proxy for successful bookings, as in "
      "Biswas et al. (2020) and Sengupta et al. (2021). We ask which listing and host features predict it, and whether the "
      "published predictors hold in London and Paris."),
    grid([["", "London", "Paris"],
          ["Listings in the snapshot"] + [log[c]["listings.csv.gz raw rows"] for c in CITIES],
          ["Reviews in the snapshot"] + [log[c]["reviews.csv.gz raw rows"] for c in CITIES],
          ["Listings analysed (random sample, seed BU7154G11)"] + [log[c]["Listings after sampling"] for c in CITIES],
          ["Reviews of those listings"] + [log[c]["Reviews after sampling"] for c in CITIES],
          ["Comments in English"] + [f"{lang[c]['en']:.0%}" for c in CITIES]],
         [WIDTH * 0.56, WIDTH * 0.22, WIDTH * 0.22]),
    Spacer(1, 6),
    p("Reviews were aggregated to one row per listing and left-joined to the listings, so never-reviewed listings stay in; "
      "comment counts match <i>number_of_reviews</i> for every listing. Host response time and instant booking are empty in "
      "both files and cannot be tested. Listings without a price have a median of "
      f"{price['London'].loc[1, 'median_availability_365']:.0f} available days (London), so a missing price means a closed listing: "
      "it is median-filled and flagged. Prices are in GBP and EUR."),
    figure("01_never_reviewed.png", "Figure 1. Share of listings by lifetime number of reviews.", scale=0.72),

    p("2. Method", "h1"),
    p("The outcome is a count with many zeros and a long tail. Poisson assumes variance equals the mean; here it is "
      f"{mfit['London'].loc['predicted share of zeros', 'Poisson']:.0%} predicted zeros against {pct(zero['London'])} observed in London. "
      "The Negative Binomial reproduces the distribution and has a far lower AIC in both cities, so all main models use it, "
      "with standard errors clustered by host. Effects are incidence rate ratios (IRR): 1.5× means 50% more expected reviews."),
    figure("02_why_negative_binomial.png", "Figure 2. Observed and predicted distribution of reviews."),
    p("Model A uses every listing and the host and listing features. Model A+ adds description and host-profile variables, "
      "Model B adds review scores and sentiment for reviewed listings, and a hurdle model separates the first review from later ones."),

    PageBreak(),
    p("3. Findings", "h1"),
    figure("03_drivers.png", "Figure 3. Model A, Negative Binomial on all listings, 95% confidence intervals."),
    p("The same features lead in both cities. Entire homes collect fewer reviews than private rooms, especially in Paris, "
      "and higher prices cost more reviews in London than in Paris."),
    figure("04_first_vs_more.png", "Figure 4. Hurdle model: any review (logit, odds ratios) and how many (zero-truncated Negative Binomial)."),
    p("Superhost status and amenities help at both stages. Entire homes are not penalised in getting a first review, only in "
      "collecting more, so support for never-reviewed listings should target the first booking."),
    figure("06_tenure_lifetime_vs_recent.png", "Figure 5. Model A on lifetime reviews and on reviews in the last 12 months."),
    figure("05_host_levers.png", "Figure 6. Average predicted reviews with one feature changed for every listing."),
    p(f"Making every host a superhost raises expected reviews by {lift['London']:.0%} in London and {lift['Paris']:.0%} in Paris. "
      "Superhost status partly results from good reviews, so this is an association, not a guaranteed effect."),

    PageBreak(),
    p("4. Does past research hold?", "h1"),
    figure("07_replication_scorecard.png", "Figure 7. Published directions against our estimates (significant at 5%)."),
    p("The overall rating reverses because ratings cluster near 5.0 and listings with few reviews tend to have perfect scores. "
      "Communication and cleanliness scores behave as Sengupta et al. report."),
    p("Where London and Paris differ", "h2"),
    grid([["Predictor", "London IRR", "Paris IRR", "Interaction p"]] +
         [[v, x(r["London IRR"]), x(r["Paris IRR"]), "< 0.001" if r["interaction p"] < .001 else f"{r['interaction p']:.3f}"]
          for v, r in pooled.rename(index={"superhost": "Superhost", "host_years_z": "Host tenure", "log_host_listings_z": "Host's listings",
                                            "accommodates_z": "Capacity", "n_amenities_z": "Amenities", "entire_home": "Entire home",
                                            "log_price_z": "Price", "price_missing": "No price"}).iterrows()],
         [WIDTH * 0.4, WIDTH * 0.2, WIDTH * 0.2, WIDTH * 0.2]),
    p("Pooled Model A with a city interaction on every predictor; p below 0.05 means the effect differs between the cities.", "small"),

    KeepTogether([p("5. Robustness", "h1"), bullets([
        "OLS on log(1 + reviews) agrees with the Negative Binomial on the direction and significance of superhost status, tenure, "
        "amenities, price and missing price in both cities.",
        "Replacing log price with price relative to the neighbourhood median leaves the other estimates almost unchanged.",
        f"{pct(stay['Paris'].loc[1, 'share'])} of Paris listings and {pct(stay['London'].loc[1, 'share'])} of London listings only take stays of "
        "30 nights or more; these are cheap and rarely reviewed. With a control for them, the price effect is "
        f"{x(A_stay['London'].loc['log_price_z', 'IRR'])} in London (Model A: {x(A['London'].loc['log_price_z', 'IRR'])}) and "
        f"{x(A_stay['Paris'].loc['log_price_z', 'IRR'])} in Paris (Model A: {x(A['Paris'].loc['log_price_z', 'IRR'])}).",
        f"Sentiment uses English comments only. In {int(trans.loc['Translated sample', 'comments']):,} Paris comments translated offline with "
        f"Argos Translate, {pct(trans.loc['Translated sample', 'positive_share'])} were positive against "
        f"{pct(trans.loc['English comments', 'positive_share'])} of English comments (z = {trans.loc['Translated sample', 'z']:.2f}). "
        "English-only sentiment slightly overstates positivity, but Model B barely changes when listings without an English comment are kept.",
    ])]),

    p("6. Recommendations", "h1"),
    bullets([
        "Make superhost status the first goal for new hosts.",
        "Prompt hosts to complete their amenities list and to add a profile photo.",
        "Treat listings with no bookable dates separately: they are closed, not unpopular.",
        "Focus support on the first review, which a fifth of listings never get.",
        "Give price advice by city: price matters more in London.",
    ]),
    p("Limitations", "h2"),
    p("Reviews are an imperfect proxy for bookings. The estimates are associations from one snapshot, and superhost status and "
      "review scores partly result from past bookings. Response time and instant booking could not be tested. Effects of "
      "continuous variables are per standard deviation of each city's own distribution."),
    p("References", "h2"),
    p("Biswas, B., Sengupta, P., &amp; Chatterjee, D. (2020). Examining the determinants of the count of customer reviews in "
      "peer-to-peer home-sharing platforms using clustering and count regression techniques. <i>Decision Support Systems, 135</i>, 113324.", "small"),
    p("Sengupta, P., Biswas, B., Kumar, A., Shankar, R., &amp; Gupta, S. (2021). Examining the predictors of successful Airbnb "
      "bookings with Hurdle models. <i>Journal of Business Research, 137</i>, 538–554.", "small"),
    p("Inside Airbnb (CC BY 4.0), insideairbnb.com/get-the-data. Code, data checks and full results: " + REPO + ".", "small"),
]

SimpleDocTemplate(OUT, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=20 * mm,
                  title="What gets an Airbnb listing booked? London and Paris", author="BU7154 group").build(
    story, onFirstPage=footer, onLaterPages=footer)
print("Saved", OUT)
