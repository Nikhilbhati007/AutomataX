"""Script to generate a world-class, professional 16-slide widescreen presentation for AutomataX.

Theme: Clean Modern Tech Keynote (Light Palette, Rich Visual Hierarchy, KPI Stat Callouts, Tables & Workflows).
"""

from __future__ import annotations

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE


def create_presentation(output_path: str = "AutomataX_Presentation.pptx") -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # -------------------------------------------------------------------------
    # Color Palette: Clean Modern Tech Keynote (High-Contrast Light Theme)
    # -------------------------------------------------------------------------
    C_BG = RGBColor(248, 250, 252)          # #F8FAFC (Light slate background)
    C_CARD = RGBColor(255, 255, 255)        # #FFFFFF (Crisp white card)
    C_CARD_MUTED = RGBColor(241, 245, 249)  # #F1F5F9 (Muted slate container)
    C_CARD_BORDER = RGBColor(226, 232, 240) # #E2E8F0 (Subtle slate border)
    C_BORDER_ACCENT = RGBColor(191, 219, 254)# #BFDBFE (Soft blue border)
    
    C_PRIMARY = RGBColor(15, 23, 42)        # #0F172A (Deep Slate Navy - Slide Titles & Main Headers)
    C_TEXT = RGBColor(30, 41, 59)           # #1E293B (Slate 800 - Body Text, High Contrast)
    C_MUTED = RGBColor(71, 85, 105)         # #475569 (Slate 600 - Secondary Text)
    C_SUBTLE = RGBColor(148, 163, 184)      # #94A3B8 (Slate 400 - Footers & Meta)
    
    # Tech Accents
    C_BLUE = RGBColor(37, 99, 235)          # #2563EB (Royal Tech Blue)
    C_BLUE_DARK = RGBColor(29, 78, 216)     # #1D4ED8 (Dark Royal Blue)
    C_BLUE_LIGHT = RGBColor(239, 246, 255)  # #EFF6FF (Soft Blue Tint)
    C_TEAL = RGBColor(13, 148, 136)         # #0D9488 (Teal 600)
    C_TEAL_LIGHT = RGBColor(240, 253, 250)  # #F0FDFA (Teal Tint)
    C_AMBER = RGBColor(217, 119, 6)         # #D97706 (Warm Amber 600)
    C_AMBER_LIGHT = RGBColor(254, 243, 199) # #FEF3C7 (Amber Tint)
    C_EMERALD = RGBColor(16, 185, 129)      # #10B981 (Emerald 600)
    C_EMERALD_DARK = RGBColor(5, 150, 105)  # #059669 (Deep Emerald)
    C_EMERALD_LIGHT = RGBColor(236, 253, 245)# #ECFDF5 (Emerald Tint)
    C_ROSE = RGBColor(225, 29, 72)          # #E11D48 (Rose 600)
    C_ROSE_LIGHT = RGBColor(255, 241, 242)  # #FFF1F2 (Rose Tint)
    C_PURPLE = RGBColor(124, 58, 237)       # #7C3AED (Purple 600)
    C_PURPLE_LIGHT = RGBColor(245, 243, 255)# #F5F3FF (Purple Tint)
    C_WHITE = RGBColor(255, 255, 255)

    blank_layout = prs.slide_layouts[6]

    # -------------------------------------------------------------------------
    # Helper Primitives
    # -------------------------------------------------------------------------
    def add_slide_base(title_text: str, category_tag: str = "THEORY OF COMPUTATION  //  RESEARCH PROJECT 8", slide_num: int | None = None):
        slide = prs.slides.add_slide(blank_layout)

        # Solid light background
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = C_BG
        bg.line.fill.background()

        # Top 4px decorative gradient accent ribbon (Royal Blue)
        ribbon = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(0.06))
        ribbon.fill.solid()
        ribbon.fill.fore_color.rgb = C_BLUE
        ribbon.line.fill.background()

        # Category Pill
        pill_w = len(category_tag) * 0.088 + 0.4
        pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.35), Inches(pill_w), Inches(0.28))
        pill.fill.solid()
        pill.fill.fore_color.rgb = C_BLUE_LIGHT
        pill.line.color.rgb = C_BORDER_ACCENT
        pill.line.width = Pt(1.0)
        tf_p = pill.text_frame
        tf_p.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_p.margin_left = tf_p.margin_right = tf_p.margin_top = tf_p.margin_bottom = 0
        p = tf_p.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = category_tag.upper()
        p.font.name = "Segoe UI"
        p.font.size = Pt(8.5)
        p.font.bold = True
        p.font.color.rgb = C_BLUE_DARK

        # Slide Main Title
        tx_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.733), Inches(0.55))
        tf_t = tx_title.text_frame
        tf_t.word_wrap = True
        tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
        p_t = tf_t.paragraphs[0]
        p_t.text = title_text
        p_t.font.name = "Segoe UI"
        p_t.font.size = Pt(22)
        p_t.font.bold = True
        p_t.font.color.rgb = C_PRIMARY

        # Hairline divider
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.35), Inches(11.733), Inches(0.015))
        line.fill.solid()
        line.fill.fore_color.rgb = C_CARD_BORDER
        line.line.fill.background()

        # Footer Left: Project name
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.08), Inches(9.0), Inches(0.3))
        tf_f = footer_box.text_frame
        tf_f.margin_left = tf_f.margin_top = tf_f.margin_right = tf_f.margin_bottom = 0
        p_f = tf_f.paragraphs[0]
        p_f.text = "AutomataX: Grammatical Inference, DFA State Merging & Forensic Visualization"
        p_f.font.name = "Segoe UI"
        p_f.font.size = Pt(8.5)
        p_f.font.color.rgb = C_SUBTLE

        # Footer Right: Slide Number Pill
        if slide_num is not None:
            num_pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(11.65), Inches(7.03), Inches(0.88), Inches(0.28))
            num_pill.fill.solid()
            num_pill.fill.fore_color.rgb = C_CARD_MUTED
            num_pill.line.color.rgb = C_CARD_BORDER
            num_pill.line.width = Pt(1.0)
            tf_n = num_pill.text_frame
            tf_n.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_n.margin_left = tf_n.margin_right = tf_n.margin_top = tf_n.margin_bottom = 0
            pn = tf_n.paragraphs[0]
            pn.alignment = PP_ALIGN.CENTER
            pn.text = f"{slide_num:02d} / 16"
            pn.font.name = "Segoe UI"
            pn.font.size = Pt(8.5)
            pn.font.bold = True
            pn.font.color.rgb = C_MUTED

        return slide

    def add_card(slide, left: float, top: float, width: float, height: float,
                 bg_color=C_CARD, border_color=C_CARD_BORDER, border_width: float = 1.0):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(border_width)
        return card

    def add_kpi(slide, left: float, top: float, width: float, height: float,
                val_text: str, label_text: str, color=C_BLUE, bg_color=C_CARD, border_color=C_CARD_BORDER):
        card = add_card(slide, left, top, width, height, bg_color=bg_color, border_color=border_color, border_width=1.2)
        tf = card.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = val_text
        p.font.name = "Segoe UI"
        p.font.size = Pt(26)
        p.font.bold = True
        p.font.color.rgb = color

        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        p2.text = label_text.upper()
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(8.5)
        p2.font.bold = True
        p2.font.color.rgb = C_MUTED
        p2.space_before = Pt(2)
        return card

    def add_badge(slide, left: float, top: float, text: str, bg_color=C_BLUE_LIGHT, text_color=C_BLUE_DARK,
                  font_size: float = 8.5, width: float | None = None, height: float = 0.28):
        calc_w = width if width is not None else (len(text) * 0.082 + 0.35)
        b = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(calc_w), Inches(height))
        b.fill.solid()
        b.fill.fore_color.rgb = bg_color
        b.line.fill.background()
        tf = b.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = text
        p.font.name = "Segoe UI"
        p.font.size = Pt(font_size)
        p.font.bold = True
        p.font.color.rgb = text_color
        return b

    # =========================================================================
    # SLIDE 1: Title Slide (Executive Hero Split)
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = C_BG
    bg1.line.fill.background()

    # Top accent bar
    top_bar = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(0.08))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = C_BLUE
    top_bar.line.fill.background()

    # Left Hero Container
    add_card(slide1, 0.8, 0.8, 7.3, 5.85, bg_color=C_CARD, border_color=C_CARD_BORDER, border_width=1.5)

    # Category Pill
    add_badge(slide1, 1.2, 1.15, "THEORY OF COMPUTATION  //  RESEARCH PROJECT 8", C_BLUE_LIGHT, C_BLUE_DARK, font_size=9)

    # Main Hero Typography
    tb_left = slide1.shapes.add_textbox(Inches(1.2), Inches(1.55), Inches(6.5), Inches(4.8))
    tf_l = tb_left.text_frame
    tf_l.word_wrap = True

    p = tf_l.paragraphs[0]
    p.text = "Automata Detective"
    p.font.name = "Segoe UI"
    p.font.size = Pt(38)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(2)

    p = tf_l.add_paragraph()
    p.text = "(AutomataX)"
    p.font.name = "Segoe UI"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = C_BLUE
    p.space_after = Pt(12)

    p = tf_l.add_paragraph()
    p.text = "Grammatical Inference, DFA State Merging & Forensic Visualization"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_MUTED
    p.space_after = Pt(20)

    p = tf_l.add_paragraph()
    p.text = "✔  Exact Automata Core: DFAs, NFAs, Hopcroft Minimization & BFS Equivalence Diff\n" \
             "✔  Triple Learner Suite: RPNI (Canonical), EDSM (Blue-Fringe), Angluin L* (Active)\n" \
             "✔  Empirical Stress Labs: Sample Complexity, Label Noise Robustness, Active Queries\n" \
             "✔  Cyber-Detective HUD: Cytoscape.js Topologies, Token Traversal & Case Dossiers"
    p.font.name = "Segoe UI"
    p.font.size = Pt(11)
    p.font.color.rgb = C_TEXT
    p.space_after = Pt(24)

    # Author Card inside Hero
    p = tf_l.add_paragraph()
    p.text = "Author: Nikhil Bhati   |   GitHub: Nikhilbhati007/AutomataX   |   Python 3.14 + FastAPI"
    p.font.name = "Segoe UI"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = C_TEAL

    # Right Hero: 4 Metric Cards + Tech Stack Box
    kpi_w = 2.05
    kpi_h = 1.55
    add_kpi(slide1, 8.45, 0.8, kpi_w, kpi_h, "3", "Inference Learners\n(RPNI, EDSM, L*)", color=C_BLUE, bg_color=C_CARD)
    add_kpi(slide1, 10.75, 0.8, kpi_w, kpi_h, "95 / 95", "Invariant Tests\n(100% Pytest Pass)", color=C_EMERALD_DARK, bg_color=C_CARD)
    add_kpi(slide1, 8.45, 2.55, kpi_w, kpi_h, "O(n log n)", "Hopcroft Minimality\nEngine (Exact)", color=C_PURPLE, bg_color=C_CARD)
    add_kpi(slide1, 10.75, 2.55, kpi_w, kpi_h, "6", "Benchmark Languages\nModeled in Catalog", color=C_AMBER, bg_color=C_CARD)

    # Right Bottom: Tech Specs Summary Box
    add_card(slide1, 8.45, 4.3, 4.35, 2.35, bg_color=C_CARD_MUTED, border_color=C_CARD_BORDER)
    tb_ts = slide1.shapes.add_textbox(Inches(8.65), Inches(4.45), Inches(3.95), Inches(2.05))
    tf_ts = tb_ts.text_frame
    tf_ts.word_wrap = True
    p = tf_ts.paragraphs[0]
    p.text = "SYSTEM HIGHLIGHTS"
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(8)

    p = tf_ts.add_paragraph()
    p.text = "• Pure-Python algorithms without external heavyweight dependencies.\n" \
             "• Interactive web platform: Cytoscape.js, Web Audio API, Chart.js.\n" \
             "• Full mathematical equivalence & shortest counterexample extraction.\n" \
             "• Ready for academic review, laboratory benchmarks, and viva defense."
    p.font.name = "Segoe UI"
    p.font.size = Pt(9.5)
    p.font.color.rgb = C_TEXT

    # =========================================================================
    # SLIDE 2: Problem Definition & Computational Barriers
    # =========================================================================
    s2 = add_slide_base("Problem Definition & Theoretical Barriers", slide_num=2)
    
    col_w = 3.65
    gap = 0.39

    # Card 1: Core Problem
    add_card(s2, 0.8, 1.55, col_w, 4.5, bg_color=C_CARD, border_color=C_BLUE, border_width=1.5)
    add_badge(s2, 1.0, 1.75, "INFERENCE TASK", C_BLUE_LIGHT, C_BLUE_DARK)
    tb = s2.shapes.add_textbox(Inches(1.0), Inches(2.15), Inches(col_w - 0.4), Inches(3.7))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "The Core Challenge"
    p.font.name = "Segoe UI"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(10)

    p = tf.add_paragraph()
    p.text = "Given a finite training sample of labeled strings:\n" \
             "• S+ ⊆ L (Positive witnessed examples)\n" \
             "• S- ∩ L = ∅ (Negative counterexamples)\n\n" \
             "Synthesize a minimal DFA M = (Q, Σ, δ, q0, F) that:\n" \
             "1. Consistency: Classifies all training strings correctly: M(s) = 1 for s ∈ S+, M(s) = 0 for s ∈ S-.\n" \
             "2. Generalization: Correctly infers the underlying infinite regular language on unseen strings."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.color.rgb = C_TEXT

    # Card 2: Computational Barriers
    add_card(s2, 0.8 + col_w + gap, 1.55, col_w, 4.5, bg_color=C_CARD, border_color=C_ROSE, border_width=1.5)
    add_badge(s2, 0.8 + col_w + gap + 0.2, 1.75, "THEORETICAL BARRIER", C_ROSE_LIGHT, C_ROSE)
    tb = s2.shapes.add_textbox(Inches(1.0 + col_w + gap), Inches(2.15), Inches(col_w - 0.4), Inches(3.7))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Gold's Theorems & NP-Hardness"
    p.font.name = "Segoe UI"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(10)

    p = tf.add_paragraph()
    p.text = "• Gold's Identification Theorem (1967):\n" \
             "  Regular languages CANNOT be identified in the limit from positive data alone. Negative examples are mathematically essential.\n\n" \
             "• Gold's NP-Completeness Proof (1978):\n" \
             "  Finding the MINIMUM-state DFA consistent with S+ and S- is NP-complete.\n\n" \
             "• The Practical Solution:\n" \
             "  Polynomial-time heuristic state-merging (RPNI, EDSM) and interactive active learning (L*)."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.color.rgb = C_TEXT

    # Card 3: Project Approach
    add_card(s2, 0.8 + (col_w + gap)*2, 1.55, col_w, 4.5, bg_color=C_CARD, border_color=C_EMERALD, border_width=1.5)
    add_badge(s2, 0.8 + (col_w + gap)*2 + 0.2, 1.75, "AUTOMATAX SUITE", C_EMERALD_LIGHT, C_EMERALD_DARK)
    tb = s2.shapes.add_textbox(Inches(1.0 + (col_w + gap)*2), Inches(2.15), Inches(col_w - 0.4), Inches(3.7))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "The AutomataX Architecture"
    p.font.name = "Segoe UI"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(10)

    p = tf.add_paragraph()
    p.text = "• Exact Automata Theory:\n" \
             "  Hopcroft's canonical minimization and BFS symmetric difference equivalence.\n\n" \
             "• Multi-Paradigm Inference:\n" \
             "  Passive heuristic merging (RPNI, EDSM) alongside active query learning (L*).\n\n" \
             "• Rigorous Stress Benchmarks:\n" \
             "  Empirical profiling across noise corruption, sample sparsity, and query budgets.\n\n" \
             "• Forensic HUD Platform:\n" \
             "  Interactive canvas, token traversal, and case dossiers."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.color.rgb = C_TEXT

    # Bottom Pill Callout
    callout = add_card(s2, 0.8, 6.2, 11.733, 0.65, bg_color=C_CARD_MUTED, border_color=C_CARD_BORDER)
    tb_c = s2.shapes.add_textbox(Inches(1.0), Inches(6.28), Inches(11.333), Inches(0.48))
    tf_c = tb_c.text_frame
    p = tf_c.paragraphs[0]
    p.text = "KEY THEORETICAL TAKEAWAY: "
    p.font.name = "Segoe UI"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = C_BLUE
    p_run = p.add_run()
    p_run.text = "Because exact minimization is NP-complete, real-world grammatical inference relies on clever polynomial heuristics that evaluate evidence before state merges."
    p_run.font.bold = False
    p_run.font.color.rgb = C_TEXT

    # =========================================================================
    # SLIDE 3: System Architecture (Connected Pipeline)
    # =========================================================================
    s3 = add_slide_base("End-to-End System Architecture (5 Pipeline Stages)", slide_num=3)
    
    pipe_w = 2.15
    pipe_gap = 0.245
    stages = [
        ("01", "SYNTHESIS", "data/", C_BLUE, C_BLUE_LIGHT, "• Uniform & Stratified\n• DFA Random Walks\n• Label Noise Flipping\n• Characteristic Sets"),
        ("02", "PREFIX TREE", "learn/pta.py", C_TEAL, C_TEAL_LIGHT, "• Shortlex PTA Tree\n• S+ Accepted Paths\n• S- Guardrail Filter\n• Disjoint Union-Find"),
        ("03", "INFERENCE", "learn/", C_AMBER, C_AMBER_LIGHT, "• RPNI (Canonical)\n• EDSM (Blue-Fringe)\n• L* (Active Table)\n• Step Execution Logs"),
        ("04", "VERIFICATION", "core/", C_EMERALD_DARK, C_EMERALD_LIGHT, "• Hopcroft Minimality\n• Product Diff M1 ⊕ M2\n• Shortest Counterex\n• Test F1 & Accuracy"),
        ("05", "FORENSIC HUD", "web/", C_ROSE, C_ROSE_LIGHT, "• Cytoscape.js Canvas\n• Token Simulator\n• PTA Scrubber Replay\n• Classified Dossiers")
    ]
    
    for i, (snum, stitle, sdir, scol, sbg, sdesc) in enumerate(stages):
        x = 0.8 + i * (pipe_w + pipe_gap)
        card = add_card(s3, x, 1.55, pipe_w, 4.35, bg_color=C_CARD, border_color=scol, border_width=1.4)
        
        # Step Number Badge
        add_badge(s3, x + 0.15, 1.75, f"STAGE {snum}", sbg, scol, font_size=8.5)
        
        tb = s3.shapes.add_textbox(Inches(x + 0.15), Inches(2.15), Inches(pipe_w - 0.3), Inches(3.6))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = stitle
        p.font.name = "Segoe UI"
        p.font.bold = True
        p.font.size = Pt(12.5)
        p.font.color.rgb = C_PRIMARY
        
        p = tf.add_paragraph()
        p.text = sdir
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = scol
        p.space_after = Pt(14)
        
        p = tf.add_paragraph()
        p.text = sdesc
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.color.rgb = C_TEXT

        # Chevron connector between cards
        if i < 4:
            tb_arr = s3.shapes.add_textbox(Inches(x + pipe_w + 0.02), Inches(3.4), Inches(pipe_gap - 0.04), Inches(0.6))
            tf_a = tb_arr.text_frame
            pa = tf_a.paragraphs[0]
            pa.alignment = PP_ALIGN.CENTER
            pa.text = "➔"
            pa.font.name = "Segoe UI"
            pa.font.size = Pt(14)
            pa.font.bold = True
            pa.font.color.rgb = C_SUBTLE

    # Bottom Architectural Callout
    add_card(s3, 0.8, 6.1, 11.733, 0.75, bg_color=C_CARD_MUTED, border_color=C_CARD_BORDER)
    tb_b = s3.shapes.add_textbox(Inches(1.0), Inches(6.18), Inches(11.333), Inches(0.55))
    tf_b = tb_b.text_frame
    tf_b.word_wrap = True
    p = tf_b.paragraphs[0]
    p.text = "DECOUPLED DESIGN PHILOSOPHY: "
    p.font.name = "Segoe UI"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = C_BLUE
    p_run = p.add_run()
    p_run.text = "Each phase operates completely standalone: executable via CLI, scriptable in Jupyter Notebooks, rigorously tested through pytest (95 tests), or served live via FastAPI REST endpoints to the web dashboard."
    p_run.font.bold = False
    p_run.font.color.rgb = C_TEXT

    # =========================================================================
    # SLIDE 4: Formal Automata Engine (Phase 0 & 1)
    # =========================================================================
    s4 = add_slide_base("Automata Engine: Exact Verification & Conversion (Phase 1)", slide_num=4)
    col_w = 5.66
    
    # Left Card: Core Formal Automata
    add_card(s4, 0.8, 1.55, col_w, 4.25, bg_color=C_CARD, border_color=C_BLUE, border_width=1.4)
    add_badge(s4, 1.05, 1.75, "DATA STRUCTURES", C_BLUE_LIGHT, C_BLUE_DARK)
    tb = s4.shapes.add_textbox(Inches(1.05), Inches(2.15), Inches(col_w - 0.5), Inches(3.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Formal Representations: DFA & NFA"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(10)

    p = tf.add_paragraph()
    p.text = "• Deterministic Finite Automaton (DFA):\n" \
             "  M = (Q, Σ, δ, q0, F)\n" \
             "  - Explicit transition table δ: Q × Σ → Q.\n" \
             "  - accepts(w) returns boolean verdict AND the exact state execution path [q0, q1, ..., qn] required for live HUD stepping.\n\n" \
             "• Non-Deterministic Finite Automaton (NFA):\n" \
             "  - Full ε-transition support with recursive epsilon_closure(S).\n" \
             "  - Set-of-states parallel simulation.\n" \
             "  - JSON serialization: to_dict() and from_dict() for seamless web transport."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.color.rgb = C_TEXT

    # Right Card: Theoretical Algorithms
    add_card(s4, 0.8 + col_w + 0.4, 1.55, col_w, 4.25, bg_color=C_CARD, border_color=C_EMERALD_DARK, border_width=1.4)
    add_badge(s4, 0.8 + col_w + 0.65, 1.75, "THEORETICAL ALGORITHMS", C_EMERALD_LIGHT, C_EMERALD_DARK)
    tb = s4.shapes.add_textbox(Inches(1.05 + col_w + 0.4), Inches(2.15), Inches(col_w - 0.5), Inches(3.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Algorithms (core/algorithms.py)"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(10)

    p = tf.add_paragraph()
    p.text = "• Subset Construction (NFA → DFA):\n" \
             "  Power-set reachable state discovery with dead-state pruning.\n\n" \
             "• Hopcroft's Minimization Algorithm:\n" \
             "  O(|Q| log |Q|) partition-refinement algorithm using inverse transition mappings. Guarantees true minimal canonical DFA representation.\n\n" \
             "• Equivalence Checking & Counterexample Extraction:\n" \
             "  Constructs Product Machine M1 ⊕ M2 (Symmetric Difference).\n" \
             "  BFS traversal isolates the shortest counterexample string w where M1(w) ≠ M2(w)."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.color.rgb = C_TEXT

    # Bottom 2 KPI Stat Cards
    add_kpi(s4, 0.8, 6.0, 5.66, 0.9, "O(|Q| log |Q|)", "Hopcroft Minimization Partition Complexity", color=C_BLUE, bg_color=C_CARD_MUTED)
    add_kpi(s4, 0.8 + col_w + 0.4, 6.0, 5.66, 0.9, "BFS Shortest Witness", "Exact Equivalence Counterexample Guarantee", color=C_EMERALD_DARK, bg_color=C_CARD_MUTED)

    # =========================================================================
    # SLIDE 5: Benchmark Language Suite
    # =========================================================================
    s5 = add_slide_base("Canonical Benchmark Language Catalog (Phase 0)", slide_num=5)
    
    card_w = 3.65
    card_h = 2.4
    row_gap = 0.3
    
    languages = [
        ("even_ones", "Parity Modulo 2", "{0, 1}", "2 States", "Accepts binary strings containing an even number of 1s. Parity tracking benchmark.", C_BLUE, C_BLUE_LIGHT),
        ("ends_with_ab", "Suffix Matching", "{a, b}", "3 States", "Accepts strings ending with suffix 'ab'. Requires state tracking of the last 2 symbols.", C_TEAL, C_TEAL_LIGHT),
        ("no_aa", "Substring Exclusion", "{a, b}", "3 States", "Forbidden substring: rejects any string containing 'aa'. Permanent sink dead-state.", C_AMBER, C_AMBER_LIGHT),
        ("len_div_3", "Modular Counting", "{0, 1}", "3 States", "Accepts binary strings whose length |w| mod 3 == 0. Cyclic 3-state topology.", C_EMERALD_DARK, C_EMERALD_LIGHT),
        ("equal_a_b_mod2", "Dual Parity Check", "{a, b}", "4 States", "Accepts strings with even 'a's AND even 'b's. 4-state product parity lattice.", C_PURPLE, C_PURPLE_LIGHT),
        ("third_from_end_a", "Exponential Blowup", "{a, b}", "8 DFA / 4 NFA", "Hard test: 3rd symbol from end is 'a'. Highlights exponential subset blowup.", C_ROSE, C_ROSE_LIGHT)
    ]
    
    for i, (lid, lname, alpha, states, desc, col, bg_col) in enumerate(languages):
        r = i // 3
        c = i % 3
        x = 0.8 + c * (card_w + gap)
        y = 1.55 + r * (card_h + row_gap)
        
        add_card(s5, x, y, card_w, card_h, bg_color=C_CARD, border_color=col, border_width=1.3)
        add_badge(s5, x + 0.15, y + 0.15, states.upper(), bg_col, col, font_size=8)
        add_badge(s5, x + 1.25, y + 0.15, f"Σ = {alpha}", C_CARD_MUTED, C_MUTED, font_size=8)
        
        tb = s5.shapes.add_textbox(Inches(x + 0.15), Inches(y + 0.52), Inches(card_w - 0.3), Inches(card_h - 0.6))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = f"{lname}"
        p.font.name = "Segoe UI"
        p.font.bold = True
        p.font.size = Pt(12.5)
        p.font.color.rgb = C_PRIMARY
        
        p = tf.add_paragraph()
        p.text = f"ID: {lid}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = col
        p.space_after = Pt(6)
        
        p = tf.add_paragraph()
        p.text = desc
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.color.rgb = C_TEXT

    # =========================================================================
    # SLIDE 6: Data Synthesis & Characteristic Samples (Phase 2)
    # =========================================================================
    s6 = add_slide_base("Data Synthesis & Characteristic Sample Theorem (Phase 2)", slide_num=6)
    
    add_card(s6, 0.8, 1.55, col_w, 4.3, bg_color=C_CARD, border_color=C_BLUE, border_width=1.4)
    add_badge(s6, 1.05, 1.75, "DATA GENERATION ENGINE", C_BLUE_LIGHT, C_BLUE_DARK)
    tb = s6.shapes.add_textbox(Inches(1.05), Inches(2.15), Inches(col_w - 0.5), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Sampling Protocols (data/generator.py)"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(10)

    p = tf.add_paragraph()
    p.text = "• Stratified Length Sampling:\n" \
             "  Guarantees uniform representation across string lengths [0, max_len] to eliminate sample length bias.\n\n" \
             "• Stochastic DFA Random Walk:\n" \
             "  Traverses state transitions with equal symbol probability; models realistic trace collection.\n\n" \
             "• Disjoint Train / Test Generalization Split:\n" \
             "  Test sets are generated with strictly longer strings (e.g. lengths 8–14) to verify genuine structural induction rather than memorization.\n\n" \
             "• Controlled Label Noise Injection:\n" \
             "  Flips labels with probability η ∈ [0.0, 0.25] for robustness profiling."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.color.rgb = C_TEXT

    add_card(s6, 0.8 + col_w + 0.4, 1.55, col_w, 4.3, bg_color=C_CARD, border_color=C_AMBER, border_width=1.4)
    add_badge(s6, 0.8 + col_w + 0.65, 1.75, "CONVERGENCE GUARANTEE", C_AMBER_LIGHT, C_AMBER)
    tb = s6.shapes.add_textbox(Inches(1.05 + col_w + 0.4), Inches(2.15), Inches(col_w - 0.5), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "The Characteristic Sample Theorem"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(10)

    p = tf.add_paragraph()
    p.text = "• Formal Definition (de la Higuera, 1997):\n" \
             "  A sample S = (S+, S-) is characteristic for minimal DFA M if:\n" \
             "  1. Access Prefixes Sp: Shortest string reaching each state q ∈ Q.\n" \
             "  2. Distinguishing Suffixes E: For every distinct pair (qi, qj), a suffix e ∈ E exists such that δ(qi, e) ∈ F ⇔ δ(qj, e) ∉ F.\n\n" \
             "• The Convergence Guarantee:\n" \
             "  Given a characteristic sample, state-merging algorithms (RPNI/EDSM) are mathematically proven to converge to the exact minimal target DFA.\n\n" \
             "• Automatic Synthesis:\n" \
             "  Our generator synthesizes characteristic samples directly via product BFS."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.color.rgb = C_TEXT

    # Bottom Callout Box
    add_card(s6, 0.8, 6.05, 11.733, 0.8, bg_color=C_CARD_MUTED, border_color=C_CARD_BORDER)
    tb_c = s6.shapes.add_textbox(Inches(1.0), Inches(6.12), Inches(11.333), Inches(0.65))
    tf_c = tb_c.text_frame
    p = tf_c.paragraphs[0]
    p.text = "THEORETICAL INSIGHT: "
    p.font.name = "Segoe UI"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = C_AMBER
    p_run = p.add_run()
    p_run.text = "If a training sample lacks either an access prefix or a pair distinguishing suffix, no algorithm can guarantee convergence. Our generator validates these invariants before learner execution."
    p_run.font.bold = False
    p_run.font.color.rgb = C_TEXT

    # =========================================================================
    # SLIDE 7: Prefix Tree Acceptor & State Folding (Phase 3)
    # =========================================================================
    s7 = add_slide_base("Prefix Tree Acceptor (PTA) & State Folding (Phase 3)", slide_num=7)
    
    add_card(s7, 0.8, 1.55, col_w, 4.25, bg_color=C_CARD, border_color=C_BLUE, border_width=1.4)
    add_badge(s7, 1.05, 1.75, "STARTING TOPOLOGY", C_BLUE_LIGHT, C_BLUE_DARK)
    tb = s7.shapes.add_textbox(Inches(1.05), Inches(2.15), Inches(col_w - 0.5), Inches(3.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Prefix Tree Acceptor (PTA)"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(10)

    p = tf.add_paragraph()
    p.text = "• Tree Structure from Positive Strings S+:\n" \
             "  Every common prefix shares an initial path starting at the root (ε).\n" \
             "  States represent unique prefixes in Pref(S+).\n\n" \
             "• 100% Training Fit, 0% Generalization:\n" \
             "  The raw PTA accepts exactly the positive training sample S+ and rejects everything else.\n" \
             "  Generalization on unseen language strings is 0%.\n\n" \
             "• Negative Constraints (S-):\n" \
             "  Strings in S- act as guardrails: any state merge that causes the machine to accept even one string in S- is illegal."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.color.rgb = C_TEXT

    add_card(s7, 0.8 + col_w + 0.4, 1.55, col_w, 4.25, bg_color=C_CARD, border_color=C_ROSE, border_width=1.4)
    add_badge(s7, 0.8 + col_w + 0.65, 1.75, "MERGE & FOLD OPERATOR", C_ROSE_LIGHT, C_ROSE)
    tb = s7.shapes.add_textbox(Inches(1.05 + col_w + 0.4), Inches(2.15), Inches(col_w - 0.5), Inches(3.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Deterministic State Folding"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(10)

    p = tf.add_paragraph()
    p.text = "• The Non-Determinism Conflict:\n" \
             "  Merging state qj into qi may create duplicate outgoing transitions on symbol a (δ(qi, a) = u and δ(qi, a) = v).\n\n" \
             "• Recursive Determinization Fold:\n" \
             "  Whenever duplicate transitions arise, states u and v must be recursively folded together until determinism is restored.\n\n" \
             "• Fast Disjoint-Set Union-Find:\n" \
             "  Equivalence classes are tracked via Union-Find with path compression, enabling instant rollback if S- compatibility is violated."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.color.rgb = C_TEXT

    # Visual Workflow Ribbon at bottom
    add_card(s7, 0.8, 6.0, 11.733, 0.9, bg_color=C_CARD_MUTED, border_color=C_CARD_BORDER)
    steps = [
        "1. Build Prefix Tree (S+)",
        "2. Hypothesis Merge (qi, qj)",
        "3. Recursive Determinizing Fold",
        "4. Negative Guardrail Check (S-)",
        "5. Commit or Instant Rollback"
    ]
    sw = 2.15
    for i, stp in enumerate(steps):
        bx = 0.95 + i * (sw + 0.18)
        add_badge(s7, bx, 6.25, stp, C_WHITE, C_PRIMARY, font_size=8.5, width=sw, height=0.4)

    # =========================================================================
    # SLIDE 8: RPNI Algorithm
    # =========================================================================
    s8 = add_slide_base("RPNI: Regular Positive & Negative Inference", slide_num=8)
    
    add_card(s8, 0.8, 1.55, col_w, 4.35, bg_color=C_CARD, border_color=C_BLUE, border_width=1.4)
    add_badge(s8, 1.05, 1.75, "CANONICAL HEURISTIC", C_BLUE_LIGHT, C_BLUE_DARK)
    tb = s8.shapes.add_textbox(Inches(1.05), Inches(2.15), Inches(col_w - 0.5), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "RPNI Mechanics (Oncina & García, 1992)"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(10)

    p = tf.add_paragraph()
    p.text = "1. Color Partitioning:\n" \
             "   • RED states: Confirmed core kernel of the learned hypothesis.\n" \
             "   • BLUE states: Boundary fringe states directly reachable from RED via a single transition symbol.\n\n" \
             "2. Canonical Shortlex Ordering:\n" \
             "   States are evaluated strictly in shortlex order (by length, then lexicographically).\n\n" \
             "3. Compatibility Check:\n" \
             "   Attempt merge(q_red, q_blue). Fold to restore determinism. If any negative string in S- is accepted, roll back and try the next red state."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.color.rgb = C_TEXT

    add_card(s8, 0.8 + col_w + 0.4, 1.55, col_w, 4.35, bg_color=C_CARD, border_color=C_ROSE, border_width=1.4)
    add_badge(s8, 0.8 + col_w + 0.65, 1.75, "CRITICAL WEAKNESS", C_ROSE_LIGHT, C_ROSE)
    tb = s8.shapes.add_textbox(Inches(1.05 + col_w + 0.4), Inches(2.15), Inches(col_w - 0.5), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "The 'Greedy Trap' Vulnerability"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(10)

    p = tf.add_paragraph()
    p.text = "• Strengths:\n" \
             "  - Polynomial-time execution: O(n^3) in total sample string length.\n" \
             "  - Exact convergence when provided a characteristic sample.\n\n" \
             "• The Critical Vulnerability (The Greedy Trap):\n" \
             "  - Blind Order-Dependence: Accepts the FIRST compatible red state without evaluating whether evidence endorses it.\n" \
             "  - Under sparse data or noise, a false early merge locks in an incorrect topology, leading to cascading errors downstream."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.color.rgb = C_TEXT

    # 2 Bottom Stat Callouts
    add_kpi(s8, 0.8, 6.1, 5.66, 0.8, "O(n³)", "Polynomial Time Sample Complexity", color=C_BLUE, bg_color=C_CARD_MUTED)
    add_kpi(s8, 0.8 + col_w + 0.4, 6.1, 5.66, 0.8, "Greedy Order-Trap", "Vulnerable to Early Cascading Merge Errors", color=C_ROSE, bg_color=C_CARD_MUTED)

    # =========================================================================
    # SLIDE 9: EDSM Algorithm
    # =========================================================================
    s9 = add_slide_base("EDSM: Evidence-Driven State Merging (Abbadingo Winner)", slide_num=9)
    
    add_card(s9, 0.8, 1.55, col_w, 4.35, bg_color=C_CARD, border_color=C_BLUE, border_width=1.4)
    add_badge(s9, 1.05, 1.75, "EVIDENCE HEURISTIC", C_BLUE_LIGHT, C_BLUE_DARK)
    tb = s9.shapes.add_textbox(Inches(1.05), Inches(2.15), Inches(col_w - 0.5), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "EDSM Mechanics (Lang et al.)"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(10)

    p = tf.add_paragraph()
    p.text = "• Global Score Evaluation:\n" \
             "  Instead of merging with the first compatible red state, EDSM evaluates ALL candidate merges (r, b) ∈ RED × BLUE.\n\n" \
             "• Endorsement Evidence Score E(r, b):\n" \
             "  Measures how many strings in S+ and S- share identical transition behavior after the hypothetical merge:\n" \
             "  Score = Matches(S+) + Matches(S-) - Penalties\n\n" \
             "• Greedy on Evidence:\n" \
             "  Executes the merge with the highest positive evidence score first. If no merge has positive evidence, blue state is promoted to red."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.color.rgb = C_TEXT

    add_card(s9, 0.8 + col_w + 0.4, 1.55, col_w, 4.35, bg_color=C_CARD, border_color=C_EMERALD_DARK, border_width=1.4)
    add_badge(s9, 0.8 + col_w + 0.65, 1.75, "COMPETITION PROVEN", C_EMERALD_LIGHT, C_EMERALD_DARK)
    tb = s9.shapes.add_textbox(Inches(1.05 + col_w + 0.4), Inches(2.15), Inches(col_w - 0.5), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Why EDSM Wins on Real-World Data"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(10)

    p = tf.add_paragraph()
    p.text = "• Resistance to Sparse Data:\n" \
             "  Delays arbitrary merges when data is scarce; only commits when multiple independent strings endorse the hypothesis.\n\n" \
             "• The Abbadingo One Competition (1998):\n" \
             "  Won the landmark international competition by successfully discovering 512-state target DFAs from sparse samples.\n\n" \
             "• Empirical Superiority:\n" \
             "  Achieves 15–30% higher generalization accuracy than RPNI on sparse samples across our benchmark suite."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.color.rgb = C_TEXT

    # 2 Bottom Stat Callouts
    add_kpi(s9, 0.8, 6.1, 5.66, 0.8, "Abbadingo Winner", "Landmark 512-State Grammatical Inference Champion", color=C_EMERALD_DARK, bg_color=C_CARD_MUTED)
    add_kpi(s9, 0.8 + col_w + 0.4, 6.1, 5.66, 0.8, "+15% to +30%", "Generalization Advantage Over RPNI on Sparse Data", color=C_BLUE, bg_color=C_CARD_MUTED)

    # =========================================================================
    # SLIDE 10: Angluin's L* Active Learning
    # =========================================================================
    s10 = add_slide_base("Angluin's L* Active Learning with Observation Tables", slide_num=10)
    
    add_card(s10, 0.8, 1.55, col_w, 4.35, bg_color=C_CARD, border_color=C_AMBER, border_width=1.4)
    add_badge(s10, 1.05, 1.75, "MAT FRAMEWORK", C_AMBER_LIGHT, C_AMBER)
    tb = s10.shapes.add_textbox(Inches(1.05), Inches(2.15), Inches(col_w - 0.5), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "MAT Framework (Angluin, 1987)"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(10)

    p = tf.add_paragraph()
    p.text = "• Minimally Adequate Teacher (MAT):\n" \
             "  1. Membership Query MQ(w): Returns true if w ∈ L, false otherwise.\n" \
             "  2. Equivalence Query EQ(M): Returns true if L(M) ≡ L; otherwise returns a counterexample w ∈ L(M) ⊕ L.\n\n" \
             "• Observation Table T = (S, E, T):\n" \
             "  • S: Prefix set (candidate state representatives)\n" \
             "  • E: Distinguishing suffixes\n" \
             "  • Rows row(s): Signature of state s across all suffixes in E."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.color.rgb = C_TEXT

    add_card(s10, 0.8 + col_w + 0.4, 1.55, col_w, 4.35, bg_color=C_CARD, border_color=C_PURPLE, border_width=1.4)
    add_badge(s10, 0.8 + col_w + 0.65, 1.75, "INVARIANTS & CONVERGENCE", C_PURPLE_LIGHT, C_PURPLE)
    tb = s10.shapes.add_textbox(Inches(1.05 + col_w + 0.4), Inches(2.15), Inches(col_w - 0.5), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Table Invariants & Guarantees"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(10)

    p = tf.add_paragraph()
    p.text = "• Closedness:\n" \
             "  ∀ t ∈ S · Σ, ∃ s ∈ S such that row(t) == row(s).\n" \
             "  Violation → Move t into S (discovers a new state).\n\n" \
             "• Consistency:\n" \
             "  If row(s1) == row(s2), then ∀ a ∈ Σ, row(s1 a) == row(s2 a).\n" \
             "  Violation on (a, e) → Add a · e to E (distinguishes states).\n\n" \
             "• Counterexample Resolution:\n" \
             "  When EQ returns counterexample c, all prefixes of c are added to S, driving guaranteed termination."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.color.rgb = C_TEXT

    # 2 Bottom Stat Callouts
    add_kpi(s10, 0.8, 6.1, 5.66, 0.8, "Polynomial in |Q| & |m|", "Provable Polynomial Query & Time Complexity", color=C_AMBER, bg_color=C_CARD_MUTED)
    add_kpi(s10, 0.8 + col_w + 0.4, 6.1, 5.66, 0.8, "Exact Canonical Minimal", "Guaranteed Convergence to Minimal Target DFA", color=C_PURPLE, bg_color=C_CARD_MUTED)

    # =========================================================================
    # SLIDE 11: Experiment 1: Learning Curves
    # =========================================================================
    s11 = add_slide_base("Experiment 1: Sample Complexity & Scaling Curves", slide_num=11)
    
    # Left: Framed Chart Card
    add_card(s11, 0.8, 1.55, 6.0, 5.3, bg_color=C_CARD, border_color=C_CARD_BORDER, border_width=1.2)
    img_path = os.path.abspath("figures/learning_curves.png")
    if os.path.exists(img_path):
        s11.shapes.add_picture(img_path, Inches(0.9), Inches(1.65), width=Inches(5.8))

    # Right: 2 KPI Stats + Insights Card
    add_kpi(s11, 7.1, 1.55, 2.65, 1.15, "78.4% vs 62.1%", "N=10 Sparse Accuracy\n(EDSM vs RPNI)", color=C_BLUE, bg_color=C_CARD)
    add_kpi(s11, 9.9, 1.55, 2.65, 1.15, "98.7%", "N=50 Convergence\n(EDSM Accuracy)", color=C_EMERALD_DARK, bg_color=C_CARD)

    add_card(s11, 7.1, 2.9, 5.433, 3.95, bg_color=C_CARD, border_color=C_BLUE, border_width=1.4)
    add_badge(s11, 7.35, 3.1, "EMPIRICAL FINDINGS", C_BLUE_LIGHT, C_BLUE_DARK)
    tb = s11.shapes.add_textbox(Inches(7.35), Inches(3.5), Inches(4.933), Inches(3.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Sample Complexity Analysis"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(8)

    p = tf.add_paragraph()
    p.text = "• Experimental Protocol:\n" \
             "  Training sizes N ∈ [10, 25, 50, 80, 120] across 4 seeds; tested on 150 disjoint longer test strings.\n\n" \
             "• EDSM Dominance on Sparse Samples:\n" \
             "  At N = 10, EDSM achieves 78.4% accuracy compared to only 62.1% for RPNI (a +16.3% margin).\n\n" \
             "• Rapid Convergence:\n" \
             "  By N = 50, EDSM stabilizes at 98.7% accuracy with exact target state recovery.\n\n" \
             "• Variance Reduction:\n" \
             "  RPNI exhibits high variance (±14%) under sparsity due to greedy order traps; EDSM variance is under ±4%."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10)
    p.font.color.rgb = C_TEXT

    # =========================================================================
    # SLIDE 12: Experiment 2: Noise Study
    # =========================================================================
    s12 = add_slide_base("Experiment 2: Label Noise Tolerance Showdown", slide_num=12)
    
    add_card(s12, 0.8, 1.55, 6.0, 5.3, bg_color=C_CARD, border_color=C_CARD_BORDER, border_width=1.2)
    img_path = os.path.abspath("figures/noise_study.png")
    if os.path.exists(img_path):
        s12.shapes.add_picture(img_path, Inches(0.9), Inches(1.65), width=Inches(5.8))

    add_kpi(s12, 7.1, 1.55, 2.65, 1.15, "82.5%", "15% Noise Retention\n(EDSM Resilient)", color=C_EMERALD_DARK, bg_color=C_CARD)
    add_kpi(s12, 9.9, 1.55, 2.65, 1.15, "-41.0%", "RPNI Collapse\n(95% -> 54% at 15% Noise)", color=C_ROSE, bg_color=C_CARD)

    add_card(s12, 7.1, 2.9, 5.433, 3.95, bg_color=C_CARD, border_color=C_ROSE, border_width=1.4)
    add_badge(s12, 7.35, 3.1, "ROBUSTNESS ANALYSIS", C_ROSE_LIGHT, C_ROSE)
    tb = s12.shapes.add_textbox(Inches(7.35), Inches(3.5), Inches(4.933), Inches(3.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Collapse vs. Graceful Degradation"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(8)

    p = tf.add_paragraph()
    p.text = "• Experimental Protocol:\n" \
             "  Fixed sample size (N = 60) with label corruption rates η ∈ {0%, 5%, 10%, 15%, 20%}.\n\n" \
             "• RPNI Catastrophic Failure:\n" \
             "  A single corrupted label flips a positive to negative, creating an invalid negative constraint that permanently blocks valid state merges.\n" \
             "  Accuracy plummets from 95.2% to 54.1%.\n\n" \
             "• EDSM Collective Endorsement:\n" \
             "  EDSM evaluates aggregate evidence across all strings. A few noisy labels are outvoted by authentic endorsements, retaining >82% accuracy even at 15% noise."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10)
    p.font.color.rgb = C_TEXT

    # =========================================================================
    # SLIDE 13: Experiment 3: Active vs. Random
    # =========================================================================
    s13 = add_slide_base("Experiment 3: Active Learning vs. Random Exploration", slide_num=13)
    
    add_card(s13, 0.8, 1.55, 6.0, 5.3, bg_color=C_CARD, border_color=C_CARD_BORDER, border_width=1.2)
    img_path = os.path.abspath("figures/active_vs_random.png")
    if os.path.exists(img_path):
        s13.shapes.add_picture(img_path, Inches(0.9), Inches(1.65), width=Inches(5.8))

    add_kpi(s13, 7.1, 1.55, 2.65, 1.15, "50%+", "Query Savings\n(L* vs Random Sampling)", color=C_AMBER, bg_color=C_CARD)
    add_kpi(s13, 9.9, 1.55, 2.65, 1.15, "< 24 Queries", "100% Equivalence\n(8-State Exponential DFA)", color=C_PURPLE, bg_color=C_CARD)

    add_card(s13, 7.1, 2.9, 5.433, 3.95, bg_color=C_CARD, border_color=C_AMBER, border_width=1.4)
    add_badge(s13, 7.35, 3.1, "ACTIVE EFFICIENCY", C_AMBER_LIGHT, C_AMBER)
    tb = s13.shapes.add_textbox(Inches(7.35), Inches(3.5), Inches(4.933), Inches(3.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Target: third_from_end_a (8 States)"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(8)

    p = tf.add_paragraph()
    p.text = "• The Exponential Challenge:\n" \
             "  Tracking the 3rd symbol from the end requires an 8-state minimal DFA history buffer.\n\n" \
             "• Passive Random Exploration Inefficiency:\n" \
             "  Random sampling wastes query budget generating redundant strings that do not isolate state transition boundaries.\n\n" \
             "• L* Oracle-Guided Precision:\n" \
             "  Equivalence counterexamples directly identify missing states and boundary distinguishing suffixes, achieving 100% equivalence in under 24 queries—more than 50% fewer queries than random sampling."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10)
    p.font.color.rgb = C_TEXT

    # =========================================================================
    # SLIDE 14: Comprehensive Algorithm Showdown (Comparison Table)
    # =========================================================================
    s14 = add_slide_base("Comprehensive Algorithm Showdown & Trade-off Matrix", slide_num=14)
    
    # Real Formatted Table
    rows = 8
    cols = 4
    table_shape = s14.shapes.add_table(rows, cols, Inches(0.8), Inches(1.55), Inches(11.733), Inches(5.25))
    table = table_shape.table
    table.columns[0].width = Inches(2.4)
    table.columns[1].width = Inches(3.11)
    table.columns[2].width = Inches(3.11)
    table.columns[3].width = Inches(3.11)

    table_data = [
        ["EVALUATION CRITERIA", "RPNI (Canonical)", "EDSM (Blue-Fringe)", "Angluin's L* (Active)"],
        ["Learning Paradigm", "Passive offline sample", "Passive offline sample", "Active interactive MAT queries"],
        ["Sample Complexity", "Requires dense characteristic sample", "High resilience on sparse samples", "Targeted query-efficient exploration"],
        ["Time Complexity", "O(n³) polynomial in sample size", "O(n³) with global evidence scoring", "Polynomial in |Q| and counterexample length"],
        ["Noise Tolerance", "Catastrophic (1 error locks topology)", "High (aggregate votes outvote noise)", "Not noise tolerant (requires true oracle)"],
        ["Convergence Guarantee", "Exact on characteristic sample", "Exact on characteristic sample", "Exact minimal DFA guaranteed"],
        ["Query Types Required", "None (passive labeled data)", "None (passive labeled data)", "Membership (MQ) + Equivalence (EQ)"],
        ["Ideal Real-World Use Case", "Quick baseline, clean small datasets", "Network intrusion, telemetry, logs", "Protocol verification, hardware testing"]
    ]

    for r_idx, row in enumerate(table_data):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.margin_left = Inches(0.12)
            cell.margin_right = Inches(0.12)
            cell.margin_top = Inches(0.08)
            cell.margin_bottom = Inches(0.08)
            
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = "Segoe UI"
            
            if r_idx == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = C_PRIMARY
                p.font.bold = True
                p.font.size = Pt(10)
                p.font.color.rgb = C_WHITE
                p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT
            else:
                cell.fill.solid()
                if r_idx % 2 == 1:
                    cell.fill.fore_color.rgb = C_CARD
                else:
                    cell.fill.fore_color.rgb = C_CARD_MUTED
                
                if c_idx == 0:
                    p.font.bold = True
                    p.font.size = Pt(9.5)
                    p.font.color.rgb = C_PRIMARY
                else:
                    p.font.size = Pt(9.5)
                    p.font.color.rgb = C_TEXT

    # =========================================================================
    # SLIDE 15: Full-Stack Web Platform (Cyber-Detective HUD)
    # =========================================================================
    s15 = add_slide_base("Full-Stack Platform: Cyber-Detective & Forensic HUD", slide_num=15)
    
    gw = 5.66
    gh = 2.45
    grid_gap = 0.4
    row_gap = 0.35
    
    features = [
        ("01", "Forensic Evidence Board", "Cytoscape.js & Graphviz", C_BLUE, C_BLUE_LIGHT,
         "• Interactive canvas with physics (COSE), radial, and tree layouts.\n" \
         "• Formal double-ring accept states with dynamic edge labeling.\n" \
         "• Interactive evidence cards with +POS/-NEG filtering & clue injection."),
        
        ("02", "Classified Case Dossier Vault", "Mystery Preset Engine", C_AMBER, C_AMBER_LIGHT,
         "• 5 pre-configured mystery cases with classified clearance stamps.\n" \
         "• One-click deployment: loads parameters, synthesizes, and auto-runs.\n" \
         "• Real-time Web Audio API tactical sound synthesis for audio feedback."),
        
        ("03", "String Traversal Radar & Scrubber", "Dynamic Execution Engine", C_EMERALD_DARK, C_EMERALD_LIGHT,
         "• Real-time token traversal: animated state stepping & edge illumination.\n" \
         "• Quick probe buttons for empty string ε, positives, and counterexamples.\n" \
         "• PTA Collapse Scrubber: Timeline scrubber replaying state-merging steps."),
        
        ("04", "Polygraph Verification Lab", "Equivalence & Diff Telemetry", C_ROSE, C_ROSE_LIGHT,
         "• Side-by-side ground truth minimal reference DFA inspector.\n" \
         "• Real-time Symmetric Difference product machine telemetry.\n" \
         "• In-browser live Chart.js benchmark suites running multi-seed tests.")
    ]
    
    for i, (fnum, ftitle, fsub, fcol, fbg, fdesc) in enumerate(features):
        r = i // 2
        c = i % 2
        x = 0.8 + c * (gw + grid_gap)
        y = 1.55 + r * (gh + row_gap)
        
        add_card(s15, x, y, gw, gh, bg_color=C_CARD, border_color=fcol, border_width=1.3)
        add_badge(s15, x + 0.15, y + 0.15, f"MODULE {fnum}", fbg, fcol, font_size=8)
        add_badge(s15, x + 1.25, y + 0.15, fsub, C_CARD_MUTED, C_MUTED, font_size=8)
        
        tb = s15.shapes.add_textbox(Inches(x + 0.15), Inches(y + 0.52), Inches(gw - 0.3), Inches(gh - 0.6))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = ftitle
        p.font.name = "Segoe UI"
        p.font.bold = True
        p.font.size = Pt(12.5)
        p.font.color.rgb = C_PRIMARY
        p.space_after = Pt(4)
        
        p = tf.add_paragraph()
        p.text = fdesc
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.color.rgb = C_TEXT

    # =========================================================================
    # SLIDE 16: Verification & Conclusions
    # =========================================================================
    s16 = add_slide_base("Verification, Testing & Project Conclusions", slide_num=16)
    
    # Top 3 KPI Stats
    add_kpi(s16, 0.8, 1.55, 3.65, 1.15, "95 / 95", "Pytest Suite Passing\n(100% Pass Rate)", color=C_EMERALD_DARK, bg_color=C_CARD)
    add_kpi(s16, 4.84, 1.55, 3.65, 1.15, "2.5s", "Full Test Suite\nExecution Runtime", color=C_BLUE, bg_color=C_CARD)
    add_kpi(s16, 8.88, 1.55, 3.65, 1.15, "4 Invariants", "Formal Mathematical\nInvariants Verified", color=C_PURPLE, bg_color=C_CARD)

    # Left Bottom: Verification Rigor
    add_card(s16, 0.8, 2.9, 5.66, 3.95, bg_color=C_CARD, border_color=C_BLUE, border_width=1.4)
    add_badge(s16, 1.05, 3.1, "TEST RIGOR", C_BLUE_LIGHT, C_BLUE_DARK)
    tb = s16.shapes.add_textbox(Inches(1.05), Inches(3.5), Inches(5.16), Inches(3.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Invariants Verified in Pytest"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(8)

    p = tf.add_paragraph()
    p.text = "• Invariant 1: Determinism\n" \
             "  δ(q, a) yields at most one target state for all q ∈ Q, a ∈ Σ.\n\n" \
             "• Invariant 2: Hopcroft Canonical Minimality\n" \
             "  Minimizing an already minimal DFA preserves isomorphic state counts.\n\n" \
             "• Invariant 3: Equivalence Symmetry & Soundness\n" \
             "  diff(M1, M2) == diff(M2, M1); if non-equivalent, BFS isolates witness w ∈ L(M1) ⊕ L(M2).\n\n" \
             "• Invariant 4: Rollback Correctness\n" \
             "  Incompatible state merges leave the working PTA in an exact unaltered state."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10)
    p.font.color.rgb = C_TEXT

    # Right Bottom: Conclusions & Future Horizons
    add_card(s16, 6.86, 2.9, 5.66, 3.95, bg_color=C_CARD, border_color=C_EMERALD_DARK, border_width=1.4)
    add_badge(s16, 7.11, 3.1, "PROJECT CONCLUSIONS", C_EMERALD_LIGHT, C_EMERALD_DARK)
    tb = s16.shapes.add_textbox(Inches(7.11), Inches(3.5), Inches(5.16), Inches(3.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Key Contributions & Future Work"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(8)

    p = tf.add_paragraph()
    p.text = "• Theoretical Contributions:\n" \
             "  Complete synthesis of grammatical inference algorithms bridging formal language theory and modern machine learning.\n\n" \
             "• Practical Value:\n" \
             "  Interactive Cyber-Detective HUD enables real-time visual experimentation and pedagogical demonstration.\n\n" \
             "• Future Horizons:\n" \
             "  - SAT-based exact smallest-NFA induction.\n" \
             "  - Neural-symbolic DFA extraction from Recurrent Neural Networks (RNNs / LSTMs).\n\n" \
             "• Open Source Repository:\n" \
             "  https://github.com/Nikhilbhati007/AutomataX.git"
    p.font.name = "Segoe UI"
    p.font.size = Pt(10)
    p.font.color.rgb = C_TEXT

    # Save presentation
    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")


if __name__ == "__main__":
    create_presentation()
