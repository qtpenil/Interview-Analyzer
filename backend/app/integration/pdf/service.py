import html
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import Flowable

# ── Palette ──────────────────────────────────────────────────────────────────
NAVY = colors.HexColor("#0F172A")
BLUE_DARK = colors.HexColor("#1E3A5F")
BLUE_MID = colors.HexColor("#2563EB")
BLUE_LIGHT = colors.HexColor("#DBEAFE")
BLUE_PALE = colors.HexColor("#EFF6FF")

GREEN_TEXT = "#15803D"
RED_TEXT = "#B91C1C"

DECISION_META = {
    "strong_hire": ("#14532D", "#DCFCE7", "STRONG HIRE"),
    "hire": ("#1E3A5F", "#DBEAFE", "HIRE"),
    "STRONG_HIRE": ("#14532D", "#DCFCE7", "STRONG HIRE"),
    "HIRE": ("#1E3A5F", "#DBEAFE", "HIRE"),
    "borderline": ("#713F12", "#FEF9C3", "BORDERLINE"),
    "BORDERLINE": ("#713F12", "#FEF9C3", "BORDERLINE"),
    "reject": ("#7F1D1D", "#FEE2E2", "NO HIRE"),
    "strong_reject": ("#450A0A", "#FEE2E2", "STRONG REJECT"),
    "STRONG_REJECT": ("#450A0A", "#FEE2E2", "STRONG REJECT"),
    "NO_HIRE": ("#7F1D1D", "#FEE2E2", "NO HIRE"),
}

SCORE_GRADIENT = [
    (0, 4, "#EF4444"),  # red
    (4, 6, "#F97316"),  # orange
    (6, 8, "#EAB308"),  # yellow
    (8, 10, "#22C55E"),  # green
]

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm

# Maximum number of bullet items considered "short" and safe to put inside a
# two-column Table cell.  If either side exceeds this, we fall back to
# rendering both columns as stacked standalone flowables so they can split
# across pages naturally.
_TWO_COL_CELL_MAX_ITEMS = 8


# ── Helpers ────────────────────────────────────────────────────────────────


def _safe(text) -> str:
    """Escape text and preserve newlines for ReportLab Paragraphs."""
    if text is None:
        return ""
    return html.escape(str(text)).replace("\n", "<br/>")


def _as_dict(obj) -> dict:
    """Best-effort conversion of pydantic models / TypedDicts / dicts to dict."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    try:
        return dict(obj)
    except Exception:
        return {}


def _enum_value(val):
    return getattr(val, "value", val)


def _fmt_score(score) -> str:
    if score is None or score == "":
        return "—"
    try:
        return f"{float(score):.1f}"
    except (TypeError, ValueError):
        return str(score)


def _safe_float(score) -> float | None:
    if score is None or score == "":
        return None
    try:
        return float(score)
    except (ValueError, TypeError):
        return None


# ── Custom flowables ──────────────────────────────────────────────────────────


class ScoreBar(Flowable):
    """Horizontal progress-bar for a single score metric (full width)."""

    BAR_H = 8
    BAR_W = 140

    def __init__(self, label: str, score, max_score: float = 10.0):
        super().__init__()
        self.label = label
        self.score = _safe_float(score)
        self.max_score = max_score
        self.width = PAGE_W - 2 * MARGIN
        self.height = 22

    def _bar_color(self):
        if self.score is None:
            return colors.HexColor("#9CA3AF")
        for lo, hi, hex_c in SCORE_GRADIENT:
            if lo <= self.score <= hi:
                return colors.HexColor(hex_c)
        return colors.HexColor("#22C55E")

    def draw(self):
        c = self.canv
        row_w = self.width
        label_w = 175
        score_w = 55
        bar_w = row_w - label_w - score_w - 16

        # Label
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#374151"))
        c.drawString(0, 5, self.label)

        # Bar background
        bx = label_w
        by = 3
        c.setFillColor(colors.HexColor("#E5E7EB"))
        c.roundRect(bx, by, bar_w, self.BAR_H, 3, stroke=0, fill=1)

        # Bar fill
        if self.score is not None:
            fill_w = bar_w * (self.score / self.max_score)
            c.setFillColor(self._bar_color())
            c.roundRect(bx, by, fill_w, self.BAR_H, 3, stroke=0, fill=1)

        # Score text
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor("#111827"))
        score_txt = f"{self.score:.1f}/10" if self.score is not None else "N/A"
        c.drawRightString(row_w, 5, score_txt)


class MiniScoreBar(Flowable):
    """Compact progress-bar for a single score metric, sized to a given width."""

    BAR_H = 6

    def __init__(self, label: str, score, width: float, max_score: float = 10.0):
        super().__init__()
        self.label = label
        self.score = _safe_float(score)
        self.max_score = max_score
        self.width = width
        self.height = 18

    def _bar_color(self):
        if self.score is None:
            return colors.HexColor("#9CA3AF")
        for lo, hi, hex_c in SCORE_GRADIENT:
            if lo <= self.score <= hi:
                return colors.HexColor(hex_c)
        return colors.HexColor("#22C55E")

    def draw(self):
        c = self.canv
        label_w = self.width * 0.46
        score_w = 34
        bar_w = max(self.width - label_w - score_w - 6, 10)

        # Label
        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.HexColor("#374151"))
        c.drawString(0, 5, self.label)

        # Bar background
        bx = label_w
        by = 3
        c.setFillColor(colors.HexColor("#E5E7EB"))
        c.roundRect(bx, by, bar_w, self.BAR_H, 2, stroke=0, fill=1)

        # Bar fill
        if self.score is not None:
            fill_w = bar_w * (self.score / self.max_score)
            c.setFillColor(self._bar_color())
            c.roundRect(bx, by, fill_w, self.BAR_H, 2, stroke=0, fill=1)

        # Score text
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(colors.HexColor("#111827"))
        score_txt = f"{self.score:.1f}" if self.score is not None else "N/A"
        c.drawRightString(self.width, 5, score_txt)


class DecisionBadge(Flowable):
    """Pill-shaped hiring decision badge."""

    def __init__(self, decision: str):
        super().__init__()
        meta = DECISION_META.get(
            str(decision).lower(),
            DECISION_META.get(
                str(decision).upper().replace(" ", "_"),
                ("#374151", "#F3F4F6", "UNKNOWN"),
            ),
        )
        self.fg_hex, self.bg_hex, self.label = meta
        self.width = PAGE_W - 2 * MARGIN
        self.height = 48

    def draw(self):
        c = self.canv
        pad_x = 20
        pill_h = 36
        pill_w = 200
        y = (self.height - pill_h) / 2

        # Pill background
        c.setFillColor(colors.HexColor(self.bg_hex))
        c.roundRect(0, y, pill_w, pill_h, pill_h / 2, stroke=0, fill=1)

        # Dot indicator
        dot_r = 6
        c.setFillColor(colors.HexColor(self.fg_hex))
        c.circle(pad_x + dot_r, y + pill_h / 2, dot_r, stroke=0, fill=1)

        # Label
        c.setFont("Helvetica-Bold", 13)
        c.setFillColor(colors.HexColor(self.fg_hex))
        c.drawString(pad_x + dot_r * 2 + 8, y + pill_h / 2 - 5, self.label)


class SectionDivider(Flowable):
    """A subtle full-width section separator with label."""

    def __init__(self, title: str):
        super().__init__()
        self.title = title
        self.width = PAGE_W - 2 * MARGIN
        self.height = 28

    def draw(self):
        c = self.canv
        # Accent bar on left
        c.setFillColor(BLUE_MID)
        c.rect(0, 10, 4, 14, stroke=0, fill=1)
        # Title
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(NAVY)
        c.drawString(12, 12, self.title.upper())
        # Rule
        c.setStrokeColor(colors.HexColor("#E5E7EB"))
        c.setLineWidth(0.5)
        c.line(0, 8, self.width, 8)


# ── Service ───────────────────────────────────────────────────────────────────


class InterviewPDFService:
    """Generates polished PDF interview assessment reports using ReportLab.

    Architecture notes
    ------------------
    ReportLab raises LayoutError when a single indivisible flowable is taller
    than the available frame height.  The two main causes are:

    1. ``KeepTogether`` wrapping large content — removed entirely.
    2. ``Table`` cells containing large ``Paragraph`` flowables.  A Table row
       cannot be split across pages, so if any cell content is taller than a
       page the build fails.

    This implementation avoids both patterns for all LLM-generated text:

    * ``candidate_answer``, ``expected_answer``, ``feedback``, ``final_feedback``,
      and ``topic feedback`` are rendered as standalone ``Paragraph`` flowables
      with the ``LongText`` style (``splitLongWords=True``, ``wordWrap="LTR"``).
      ReportLab can split plain Paragraphs across pages without any limits.

    * Bullet-item lists (concepts, strengths, weaknesses, etc.) are rendered in
      a two-column ``Table`` only when *both* sides are short (≤
      ``_TWO_COL_CELL_MAX_ITEMS`` items).  When either side is longer the method
      falls back to two standalone ``Paragraph`` blocks stacked vertically, which
      can paginate freely.

    * The compact topic overview table and the score-grid table contain only
      short strings or custom ``Flowable`` objects (``MiniScoreBar``) whose
      height is fixed and well under one page — safe in table cells.
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._register_styles()

    def _register_styles(self):
        add = self.styles.add

        add(
            ParagraphStyle(
                "RTitle",
                parent=self.styles["Title"],
                fontSize=20,
                leading=26,
                textColor=colors.white,
                spaceAfter=2,
            )
        )
        add(
            ParagraphStyle(
                "RSubtitle",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#93C5FD"),
                spaceAfter=0,
            )
        )
        add(
            ParagraphStyle(
                "Body",
                parent=self.styles["BodyText"],
                fontSize=9.5,
                leading=14,
                textColor=colors.HexColor("#374151"),
                spaceAfter=5,
            )
        )
        add(
            ParagraphStyle(
                "BodySmall",
                parent=self.styles["BodyText"],
                fontSize=8.5,
                leading=13,
                textColor=colors.HexColor("#6B7280"),
            )
        )
        # ── LongText ──────────────────────────────────────────────────────────
        # Used for ALL LLM-generated prose that may be arbitrarily long.
        # splitLongWords=True  → prevents single unbreakable tokens from
        #                        overflowing the column width.
        # wordWrap="LTR"       → standard left-to-right word-wrap, required for
        #                        correct splitting behaviour in ReportLab.
        # These two flags together ensure ReportLab can always break the
        # Paragraph across page boundaries, eliminating LayoutError for prose.
        add(
            ParagraphStyle(
                "LongText",
                parent=self.styles["BodyText"],
                fontSize=9,
                leading=13,
                textColor=colors.HexColor("#374151"),
                wordWrap="LTR",
                splitLongWords=True,
                spaceAfter=10,
            )
        )
        add(
            ParagraphStyle(
                "QLabel",
                parent=self.styles["Normal"],
                fontSize=9.5,
                leading=13,
                textColor=NAVY,
                fontName="Helvetica-Bold",
            )
        )
        add(
            ParagraphStyle(
                "QAnswer",
                parent=self.styles["Normal"],
                fontSize=9,
                leading=13,
                textColor=colors.HexColor("#4B5563"),
                leftIndent=12,
            )
        )
        add(
            ParagraphStyle(
                "InfoKey",
                parent=self.styles["Normal"],
                fontSize=9,
                fontName="Helvetica-Bold",
                textColor=colors.HexColor("#6B7280"),
            )
        )
        add(
            ParagraphStyle(
                "InfoVal",
                parent=self.styles["Normal"],
                fontSize=9.5,
                textColor=NAVY,
            )
        )
        add(
            ParagraphStyle(
                "MetaSmall",
                parent=self.styles["Normal"],
                fontSize=8,
                leading=11,
                textColor=colors.HexColor("#9CA3AF"),
            )
        )
        # ── BulletLong ────────────────────────────────────────────────────────
        # Like LongText but with a left indent used for standalone bullet lists
        # that escape the two-column table when list length is large.
        add(
            ParagraphStyle(
                "BulletLong",
                parent=self.styles["BodyText"],
                fontSize=8.5,
                leading=13,
                textColor=colors.HexColor("#374151"),
                leftIndent=6,
                wordWrap="LTR",
                splitLongWords=True,
                spaceAfter=2,
            )
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def generate(self, interview_id: str, state_dict: dict) -> io.BytesIO:

        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=MARGIN,
            leftMargin=MARGIN,
            topMargin=18 * mm,
            bottomMargin=MARGIN,
        )

        elements = []

        # ── Page 1: header · hiring decision · scores ──
        elements.extend(self._build_header(state_dict))
        elements.extend(self._build_decision_and_scores(state_dict))

        # ── a. Interview Summary (moved up, first content section) ──
        elements.extend(self._build_summary(state_dict))
        elements.append(Spacer(1, 14))

        # ── b. Topic Details ──
        elements.extend(self._build_topics_overview(state_dict))
        elements.extend(self._build_topics_detail(state_dict))
        elements.append(Spacer(1, 14))

        # ── c. Question/Answer Assessment List ──
        elements.extend(self._build_questions_list(state_dict))

        doc.build(elements)

        buffer.seek(0)

        return buffer

    # ── State accessors ──────────────────────────────────────────────────────

    def _summary_dict(self, state_dict: dict) -> dict:
        """Return the InterviewSummary payload as a plain dict (or {})."""
        return _as_dict(state_dict.get("interview_summary"))

    def _field(self, state_dict: dict, key: str, default=None):
        """Look up a value first on the top-level state, then on the
        nested interview_summary, falling back to `default`."""
        if state_dict.get(key) is not None:
            return state_dict.get(key)
        summary = self._summary_dict(state_dict)
        return summary.get(key, default)

    def _questions(self, state_dict: dict) -> list:
        items = state_dict.get("question_evaluations") or state_dict.get("questions")
        if not items:
            return []

        # Handle wrapper model/dict
        if isinstance(items, dict) and "evaluations" in items:
            items = items["evaluations"]
        elif hasattr(items, "evaluations"):
            items = items.evaluations
        elif isinstance(items, dict) and "questions" in items:
            items = items["questions"]

        if not isinstance(items, list):
            items = [items]  # fallback

        return [_as_dict(q) for q in items]

    def _topics(self, state_dict: dict) -> list:
        items = state_dict.get("topic_summaries") or state_dict.get("topics")
        if not items:
            return []

        if isinstance(items, dict):
            if "summaries" in items:
                items = items["summaries"]
            elif "topic_summaries" in items:
                items = items["topic_summaries"]
            elif "topics" in items:
                items = items["topics"]
        else:
            if hasattr(items, "summaries"):
                items = items.summaries
            elif hasattr(items, "topic_summaries"):
                items = items.topic_summaries
            elif hasattr(items, "topics"):
                items = items.topics

        if not isinstance(items, list):
            items = [items]

        return [_as_dict(t) for t in items]

    # ── Small render helpers ─────────────────────────────────────────────────

    def _labeled_bullets(self, label: str, items: list, color_hex: str) -> Paragraph:
        """Return a single Paragraph with a coloured label and bullet lines.

        Safe for use inside Table cells only when the item list is short (caller
        is responsible for the length check — see ``_two_col_safe``).
        """
        if items and isinstance(items, list):
            body = "<br/>".join(f"•  {_safe(i)}" for i in items if i)
        else:
            body = "—"
        html_str = f'<font color="{color_hex}"><b>{_safe(label)}</b></font><br/>{body}'
        return Paragraph(html_str, self.styles["BodySmall"])

    def _labeled_bullets_flowables(self, label: str, items: list, color_hex: str) -> list:
        """Return a list of standalone flowables for a labelled bullet group.

        Used instead of ``_labeled_bullets`` when the list may be long, because
        standalone Paragraphs can paginate freely while Table cell content cannot.
        """
        result = [
            Paragraph(
                f'<font color="{color_hex}"><b>{_safe(label)}</b></font>',
                self.styles["BodySmall"],
            )
        ]
        if items and isinstance(items, list):
            for item in items:
                if item:
                    result.append(
                        Paragraph(
                            f'<font color="{color_hex}">•  {_safe(item)}</font>',
                            self.styles["BulletLong"],
                        )
                    )
        else:
            result.append(Paragraph("—", self.styles["BulletLong"]))
        return result

    def _two_col(self, left_flowable, right_flowable, avail: float) -> Table:
        """Render two flowables side-by-side in a two-column Table.

        Only call this when both flowables are short (e.g. brief Paragraph
        objects).  The returned Table row cannot be split across pages, so
        tall content will cause LayoutError.
        """
        t = Table([[left_flowable, right_flowable]], colWidths=[avail / 2, avail / 2])
        t.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return t

    def _two_col_bullets(
        self,
        left_label: str,
        left_items: list,
        left_color: str,
        right_label: str,
        right_items: list,
        right_color: str,
        avail: float,
    ) -> list:
        """Render two bullet groups side-by-side if short; stacked if long.

        When either side exceeds ``_TWO_COL_CELL_MAX_ITEMS`` we fall back to
        rendering both groups as sequential standalone flowables.  This avoids
        placing tall Paragraph content inside a Table cell (which cannot be
        split across pages and would cause LayoutError).

        When both sides are short the content fits in a two-column Table row,
        preserving the original visual layout.
        """
        left_count = len(left_items) if left_items else 0
        right_count = len(right_items) if right_items else 0

        if left_count <= _TWO_COL_CELL_MAX_ITEMS and right_count <= _TWO_COL_CELL_MAX_ITEMS:
            # Both lists are short: safe to put inside a Table cell.
            return [
                self._two_col(
                    self._labeled_bullets(left_label, left_items, left_color),
                    self._labeled_bullets(right_label, right_items, right_color),
                    avail,
                )
            ]

        # One or both lists are long: render as standalone flowables so
        # ReportLab can paginate them freely across page boundaries.
        elements = []
        elements.extend(self._labeled_bullets_flowables(left_label, left_items, left_color))
        elements.append(Spacer(1, 6))
        elements.extend(self._labeled_bullets_flowables(right_label, right_items, right_color))
        return elements

    # ── Sections ──────────────────────────────────────────────────────────────

    def _build_header(self, state_dict: dict) -> list:
        """Dark banner header with candidate name and meta.

        Only short, fixed-length Paragraphs live inside the nested Table cells
        here (title, name, timestamp) — all well under one page, so the Table
        cannot trigger LayoutError.
        """
        name = self._field(state_dict, "candidate_name") or "Candidate"
        experience = self._field(state_dict, "claimed_experience_years")
        exp_text = f"{experience} yrs experience" if experience is not None else ""
        generated = datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")

        # Left col: title + name — short fixed content, safe in Table cells
        left_data = [
            [Paragraph("Interview Assessment Report", self.styles["RTitle"])],
            [
                Paragraph(
                    f"{_safe(name)}  {'·  ' + _safe(exp_text) if exp_text else ''}",
                    self.styles["RSubtitle"],
                )
            ],
            [Paragraph(f"Generated {_safe(generated)}", self.styles["RSubtitle"])],
        ]
        left_table = Table(left_data, colWidths=[PAGE_W - 2 * MARGIN])
        left_table.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 18),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 18),
                    ("TOPPADDING", (0, 0), (0, 0), 22),
                    ("BOTTOMPADDING", (0, -1), (-1, -1), 20),
                    ("BOTTOMPADDING", (0, 0), (0, 0), 2),
                    ("BOTTOMPADDING", (0, 1), (0, 1), 4),
                ]
            )
        )

        # Outer banner table
        banner = Table([[left_table]], colWidths=[PAGE_W - 2 * MARGIN])
        banner.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), BLUE_DARK),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BLUE_DARK]),
                ]
            )
        )

        return [banner, Spacer(1, 14)]

    def _build_decision_and_scores(self, state_dict: dict) -> list:
        elements = []

        # ── Decision badge ──
        decision = self._field(state_dict, "hiring_decision", "")
        if decision:
            elements.append(SectionDivider("Hiring Decision"))
            elements.append(Spacer(1, 6))
            elements.append(DecisionBadge(_enum_value(decision)))
            elements.append(Spacer(1, 14))

        # ── Score bars ──
        elements.append(SectionDivider("Score Summary"))
        elements.append(Spacer(1, 8))

        score_fields = [
            ("Overall Score", self._field(state_dict, "overall_score")),
            ("Technical", self._field(state_dict, "technical_score")),
            ("Communication", self._field(state_dict, "communication_score")),
            ("Confidence", self._field(state_dict, "confidence_score")),
            ("Knowledge Depth", self._field(state_dict, "knowledge_depth")),
            (
                "Experience Alignment",
                self._field(state_dict, "experience_alignment_score"),
            ),
        ]

        for label, score in score_fields:
            if score is not None:
                elements.append(ScoreBar(label, score))
                elements.append(Spacer(1, 4))

        elements.append(Spacer(1, 10))
        return elements

    def _build_topics_overview(self, state_dict: dict) -> list:
        """Page 1 only: compact topic summary table (no detail cards).

        Columns: Topic · Questions · Avg. Score · Confidence.
        Each cell contains only short strings/Paragraphs — no LayoutError risk.
        """
        topics = self._topics(state_dict)
        if not topics:
            return []

        avail = PAGE_W - 2 * MARGIN
        elements = [SectionDivider("Topics Covered"), Spacer(1, 8)]

        rows = [
            [
                Paragraph("<b>Topic</b>", self.styles["BodySmall"]),
                Paragraph("<b>Questions</b>", self.styles["BodySmall"]),
                Paragraph("<b>Avg. Score</b>", self.styles["BodySmall"]),
                Paragraph("<b>Confidence</b>", self.styles["BodySmall"]),
            ]
        ]
        for t in topics:
            name = t.get("topic", "")
            total_q = t.get("total_questions", "—")
            avg_score = t.get("average_score")
            conf_score = t.get("confidence_score")

            rows.append(
                [
                    Paragraph(_safe(name), self.styles["Body"]),
                    Paragraph(_safe(total_q), self.styles["Body"]),
                    Paragraph(_safe(_fmt_score(avg_score)), self.styles["Body"]),
                    Paragraph(_safe(_fmt_score(conf_score)), self.styles["Body"]),
                ]
            )

        tbl = Table(
            rows,
            colWidths=[avail * 0.40, avail * 0.18, avail * 0.21, avail * 0.21],
        )
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), BLUE_DARK),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLUE_PALE, colors.white]),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#BFDBFE")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 9),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        elements.append(tbl)
        elements.append(Spacer(1, 10))
        return elements

    def _build_topics_detail(self, state_dict: dict) -> list:
        """Page 2+: per-topic detail cards (concepts + feedback).

        Starts immediately after the PageBreak injected by generate().
        All LLM-generated feedback is rendered as standalone LongText
        Paragraphs — never inside Table cells — so it can paginate freely.
        """
        topics = self._topics(state_dict)
        if not topics:
            return []

        avail = PAGE_W - 2 * MARGIN
        elements = [SectionDivider("Topic Details"), Spacer(1, 8)]

        for t in topics:
            name = t.get("topic", "")
            strongest = t.get("strongest_concepts") or []
            weakest = t.get("weakest_concepts") or []
            feedback = t.get("feedback", "")

            # Topic name header — short, safe as standalone Paragraph
            elements.append(Paragraph(_safe(name), self.styles["QLabel"]))
            elements.append(Spacer(1, 4))

            # Concepts two-column layout with overflow protection.
            elements.extend(
                self._two_col_bullets(
                    "Strongest Concepts",
                    strongest,
                    GREEN_TEXT,
                    "Weakest Or Uncovered Concepts",
                    weakest,
                    RED_TEXT,
                    avail,
                )
            )
            elements.append(Spacer(1, 4))

            # Topic Feedback — standalone LongText Paragraph, NEVER inside a
            # Table cell. LLM feedback can be many paragraphs long; standalone
            # Paragraphs can split across pages freely.
            if feedback:
                elements.append(Paragraph("<b>Topic Feedback:</b>", self.styles["BodySmall"]))
                elements.append(Paragraph(_safe(feedback), self.styles["LongText"]))

            elements.append(Spacer(1, 10))
            elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
            elements.append(Spacer(1, 10))

        elements.append(Spacer(1, 8))
        return elements

    # Retained as a convenience alias so any external callers are not broken.
    def _build_topics_table(self, state_dict: dict) -> list:
        return self._build_topics_overview(state_dict) + self._build_topics_detail(state_dict)

    def _build_question_meta_card(
        self,
        category: str,
        sub_category: str,
        difficulty: str,
        expected_experience,
    ) -> Table:
        """Highlighted metadata card for a question.

        Light green background (#ECFDF5), dark green border (#10B981),
        bold labels, normal-weight values.  Implemented as a single-cell
        Table so ReportLab handles padding and border in one pass.
        """
        META_BG = colors.HexColor("#ECFDF5")
        META_BORDER = colors.HexColor("#10B981")
        META_TEXT = "#065F46"

        label_style = ParagraphStyle(
            "MetaCardLabel",
            parent=self.styles["BodySmall"],
            fontSize=8.5,
            leading=13,
            textColor=colors.HexColor(META_TEXT),
        )

        rows = []
        if category:
            rows.append(
                Paragraph(
                    f'<font color="{META_TEXT}"><b>Category:</b>  {_safe(category)}</font>',
                    label_style,
                )
            )
        if sub_category:
            rows.append(
                Paragraph(
                    f'<font color="{META_TEXT}"><b>Sub Category:</b>  {_safe(sub_category)}</font>',
                    label_style,
                )
            )
        if difficulty:
            rows.append(
                Paragraph(
                    f'<font color="{META_TEXT}"><b>Difficulty:</b>  {_safe(str(difficulty).title())}</font>',
                    label_style,
                )
            )
        if expected_experience is not None:
            rows.append(
                Paragraph(
                    f'<font color="{META_TEXT}"><b>Expected Experience:</b>  {_safe(expected_experience)} Years</font>',
                    label_style,
                )
            )

        if not rows:
            return None

        avail = PAGE_W - 2 * MARGIN
        # Stack all rows inside a single-cell Table for the card border/bg
        inner = Table([[r] for r in rows], colWidths=[avail - 24])
        inner.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )

        card = Table([[inner]], colWidths=[avail])
        card.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), META_BG),
                    ("BOX", (0, 0), (-1, -1), 1, META_BORDER),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        return card

    def _build_questions_list(self, state_dict: dict) -> list:
        questions = self._questions(state_dict)
        if not questions:
            return []

        avail = PAGE_W - 2 * MARGIN
        col_w = avail / 2
        bar_w = col_w - 16

        # No leading SectionDivider here — each question starts on its own page
        # with its own header, so a single top-level divider would be orphaned.
        elements = []

        for i, q in enumerate(questions, 1):
            question = q.get("question", "")
            candidate_answer = q.get("answer", "")
            expected_answer = q.get("expected_answer", "")
            category = q.get("category", "")
            sub_category = q.get("sub_category", "")
            difficulty = _enum_value(q.get("difficulty", ""))
            expected_experience = q.get("expected_experience")
            accuracy_score = q.get("accuracy_score")

            score_str = f"  ·  Accuracy: {_fmt_score(accuracy_score)}/10" if accuracy_score is not None else ""

            # ── Every question starts on a fresh page ──
            elements.append(PageBreak())
            elements.append(SectionDivider(f"Question {i}"))
            elements.append(Spacer(1, 8))

            # ── Question text ──
            elements.append(Paragraph(f"<b>Q{i}{_safe(score_str)}</b>", self.styles["InfoKey"]))
            elements.append(Paragraph(_safe(question), self.styles["QLabel"]))
            elements.append(Spacer(1, 8))

            # ── Highlighted metadata card (replaces the old plain meta line) ──
            meta_card = self._build_question_meta_card(category, sub_category, difficulty, expected_experience)
            if meta_card is not None:
                elements.append(meta_card)
            elements.append(Spacer(1, 10))

            # ── Candidate Answer — standalone LongText, never inside a Table cell.
            # Candidate answers may span multiple paragraphs / pages.
            # splitLongWords + wordWrap on LongText style ensures safe pagination.
            if candidate_answer:
                elements.append(Paragraph("<b>Candidate Answer:</b>", self.styles["BodySmall"]))
                elements.append(Paragraph(_safe(candidate_answer), self.styles["LongText"]))

            # ── Expected Answer — same reasoning as candidate_answer above.
            if expected_answer:
                elements.append(Paragraph("<b>Expected Answer:</b>", self.styles["BodySmall"]))
                elements.append(Paragraph(_safe(expected_answer), self.styles["LongText"]))

            # ── Score grid (2 columns × 3 rows of MiniScoreBar).
            # MiniScoreBar is a custom Flowable with a fixed small height (18 pt).
            # It is always well under one page — safe inside Table cells.
            score_fields = [
                ("Accuracy", q.get("accuracy_score")),
                ("Depth", q.get("depth_score")),
                ("Completeness", q.get("completeness_score")),
                ("Clarity", q.get("clarity_score")),
                ("Confidence", q.get("confidence_score")),
                ("Exp. Alignment", q.get("experience_alignment_score")),
            ]
            score_rows = []
            for j in range(0, len(score_fields), 2):
                pair = score_fields[j : j + 2]
                row: list[MiniScoreBar | str] = [MiniScoreBar(label, score, bar_w) for label, score in pair]
                while len(row) < 2:
                    row.append("")
                score_rows.append(row)

            score_table = Table(score_rows, colWidths=[col_w, col_w])
            score_table.setStyle(
                TableStyle(
                    [
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )
            elements.append(score_table)
            elements.append(Spacer(1, 6))

            # ── Concepts: strong vs missing.
            # Uses _two_col_bullets which guards against long lists automatically.
            strong_concepts = q.get("strong_concepts") or []
            missing_concepts = q.get("missing_concepts") or []
            elements.extend(
                self._two_col_bullets(
                    "Strong Concepts",
                    strong_concepts,
                    GREEN_TEXT,
                    "Missing Concepts",
                    missing_concepts,
                    RED_TEXT,
                    avail,
                )
            )
            elements.append(Spacer(1, 6))

            # ── Strengths vs weaknesses — same overflow protection.
            strengths = q.get("strengths") or []
            weaknesses = q.get("weaknesses") or []
            elements.extend(
                self._two_col_bullets(
                    "Strengths",
                    strengths,
                    GREEN_TEXT,
                    "Weaknesses",
                    weaknesses,
                    RED_TEXT,
                    avail,
                )
            )
            elements.append(Spacer(1, 6))

            # ── Feedback — standalone LongText Paragraph, never inside a Table.
            # LLM feedback is the most likely candidate for multi-page content.
            feedback = q.get("feedback", "")
            if feedback:
                elements.append(Paragraph("<b>Feedback:</b>", self.styles["BodySmall"]))
                elements.append(Paragraph(_safe(feedback), self.styles["LongText"]))

        return elements

    def _build_summary(self, state_dict: dict) -> list:
        summary = self._summary_dict(state_dict)
        final_feedback = summary.get("final_feedback") or state_dict.get("final_feedback", "")

        skills_assessed = summary.get("skills_assessed") or state_dict.get("skills_assessed") or []
        strongest_topics = summary.get("strongest_topics") or state_dict.get("strongest_topics") or []
        weakest_topics = summary.get("weakest_topics") or state_dict.get("weakest_topics") or []
        strengths = summary.get("strengths") or state_dict.get("strengths") or []
        weaknesses = summary.get("weaknesses") or state_dict.get("weaknesses") or []
        risk_factors = summary.get("risk_factors") or state_dict.get("risk_factors") or []

        if not any(
            [
                final_feedback,
                skills_assessed,
                strongest_topics,
                weakest_topics,
                strengths,
                weaknesses,
                risk_factors,
            ]
        ):
            return []

        avail = PAGE_W - 2 * MARGIN
        elements = [SectionDivider("Interview Summary"), Spacer(1, 8)]

        # ── Skills assessed — short comma-separated string, safe as Paragraph ──
        if skills_assessed:
            elements.append(Paragraph("Skills Assessed", self.styles["InfoKey"]))
            elements.append(Spacer(1, 3))
            elements.append(
                Paragraph(
                    _safe(", ".join(str(s) for s in skills_assessed)),
                    self.styles["Body"],
                )
            )
            elements.append(Spacer(1, 10))

        # ── Strongest / weakest topics — with overflow protection ──
        if strongest_topics or weakest_topics:
            elements.extend(
                self._two_col_bullets(
                    "Strongest Topics",
                    strongest_topics,
                    GREEN_TEXT,
                    "Weakest Topics",
                    weakest_topics,
                    RED_TEXT,
                    avail,
                )
            )
            elements.append(Spacer(1, 10))

        # ── Strengths / weaknesses — with overflow protection ──
        if strengths or weaknesses:
            elements.extend(
                self._two_col_bullets(
                    "Strengths",
                    strengths,
                    GREEN_TEXT,
                    "Weaknesses",
                    weaknesses,
                    RED_TEXT,
                    avail,
                )
            )
            elements.append(Spacer(1, 10))

        # ── Risk factors — rendered as standalone LongText Paragraphs.
        # Risk factor strings may be long LLM-generated sentences.
        # Keeping them as individual standalone Paragraphs (not inside a Table)
        # ensures they can split across pages without raising LayoutError.
        if risk_factors:
            elements.append(Paragraph("<b>Risk Factors:</b>", self.styles["BodySmall"]))
            for r in risk_factors:
                elements.append(
                    Paragraph(
                        f'<font color="{RED_TEXT}">• {_safe(r)}</font>',
                        self.styles["LongText"],
                    )
                )
            elements.append(Spacer(1, 10))

        # ── Final feedback — standalone LongText Paragraph.
        # final_feedback is the single most likely source of multi-page content.
        # It must NEVER be placed inside a Table cell.  As a standalone Paragraph
        # with splitLongWords=True and wordWrap="LTR" it can span as many pages
        # as necessary without any LayoutError.
        if final_feedback:
            elements.append(Paragraph("Final Assessment", self.styles["InfoKey"]))
            elements.append(Spacer(1, 4))
            elements.append(Paragraph(_safe(str(final_feedback)), self.styles["LongText"]))
            elements.append(Spacer(1, 12))

        return elements


interview_pdf_service = InterviewPDFService()
