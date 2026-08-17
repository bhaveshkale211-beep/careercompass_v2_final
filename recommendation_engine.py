# ============================================================
#   recommendation_engine.py
#   THE BRAIN of CareerCompass — Scoring & Recommendation Logic
# ============================================================
#
#   This file does ONE job:
#   Takes user inputs → Calculates a score for each career
#   → Returns ranked career list
#
#   The 5 careers we recommend:
#   1. AI / ML Engineer
#   2. Data Scientist / Analyst
#   3. Full Stack Developer
#   4. Cloud / DevOps Engineer
#   5. Cybersecurity Analyst
# ============================================================


# ── Career Details Dictionary ────────────────────────────────
# All info about each career is stored here.
# Key = short career ID used throughout the code.

CAREER_INFO = {

    "ai": {
        "key":    "ai",
        "title":  "AI / ML Engineer",
        "field":  "AI",
        "icon":   "🤖",
        "desc":   "Design and train intelligent systems using machine learning. One of the highest-growing fields globally.",
        "salary": "₹6–18 LPA",
        "demand": "🔥 Very High",
        "fill_color": "#a78bfa",
        # Why this career suits each persona type
        "why": {
            "non-it":         "Your curiosity and analytical thinking are the real starting points — Python can be learned by anyone!",
            "career-changer": "Your domain expertise + AI is a rare and very valuable combo in today's market.",
            "career-gap":     "AI tools have never been more accessible — great time to re-enter.",
            "undergraduate":  "Internships in AI are booming — start with Python and Kaggle today.",
            "graduate":       "Strong demand for entry-level ML roles — even without experience, projects win.",
            "professional":   "AI skills multiply the value of any IT career.",
            "default":        "Your logic and analytical mindset are a natural fit for AI/ML."
        }
    },

    "data": {
        "key":    "data",
        "title":  "Data Scientist / Analyst",
        "field":  "Data",
        "icon":   "📊",
        "desc":   "Turn raw numbers into business decisions using statistics, coding and visualisation.",
        "salary": "₹5–14 LPA",
        "demand": "🔥 High",
        "fill_color": "#34d399",
        "why": {
            "non-it":         "If you've ever used Excel or tracked data — you're already partway there!",
            "career-changer": "Your domain knowledge (finance, retail, health) + data skills = very rare talent.",
            "career-gap":     "Data skills age well. Free tools like Power BI and Python are your re-entry path.",
            "undergraduate":  "Projects and Kaggle competitions get you hired — no 2+ years experience needed.",
            "default":        "Your strengths in numbers and pattern-finding fit data science perfectly."
        }
    },

    "dev": {
        "key":    "dev",
        "title":  "Full Stack Developer",
        "field":  "Dev",
        "icon":   "💻",
        "desc":   "Build complete web apps — frontend and backend. Massive job market, very beginner-friendly.",
        "salary": "₹4–12 LPA",
        "demand": "✅ Very High",
        "fill_color": "#fb923c",
        "why": {
            "non-it":         "Development has the friendliest on-ramp — HTML is just formatting text. Start today!",
            "career-gap":     "Free bootcamps and The Odin Project let you rebuild skills in under 6 months.",
            "career-changer": "Your communication skills + development = great product developer.",
            "undergraduate":  "Build one real project and publish it — that's your resume!",
            "default":        "Your builder mindset and creative streak are exactly what dev teams look for."
        }
    },

    "cloud": {
        "key":    "cloud",
        "title":  "Cloud / DevOps Engineer",
        "field":  "Cloud",
        "icon":   "☁️",
        "desc":   "Manage infrastructure as every company moves to the cloud. Critical, well-paid, globally in demand.",
        "salary": "₹5–16 LPA",
        "demand": "✅ High",
        "fill_color": "#00d4ff",
        "why": {
            "professional":   "Cloud is the #1 growing area — pairs perfectly with any existing IT background.",
            "career-changer": "IT ops or sysadmin experience from any field gives you a real head start.",
            "non-it":         "AWS Free Tier lets you start hands-on learning for zero cost.",
            "default":        "Your organised, systematic thinking suits cloud/DevOps perfectly."
        }
    },

    "cyber": {
        "key":    "cyber",
        "title":  "Cybersecurity Analyst",
        "field":  "Cyber",
        "icon":   "🔐",
        "desc":   "Protect organisations from hackers and digital threats. High demand globally.",
        "salary": "₹5–15 LPA",
        "demand": "✅ High",
        "fill_color": "#f87171",
        "why": {
            "non-it":         "TryHackMe starts from absolute zero — many cybersecurity pros came from non-IT fields.",
            "career-gap":     "CompTIA Security+ cert is recognised globally and is a solid re-entry credential.",
            "career-changer": "Detail-oriented analytical thinkers from any field thrive in cybersecurity.",
            "default":        "Your attention to detail and investigative mindset are perfect for cybersecurity."
        }
    }
}


# ============================================================
#   MAIN FUNCTION: calculate_scores()
#
#   This function is called from app.py with the user's data.
#   It returns a dict like: {"ai": 82, "data": 75, ...}
# ============================================================

def calculate_scores(persona, edu, tech, strengths, work_style, goal, answers):
    """
    Calculate a compatibility score (0-99) for each IT career
    based on the user's background survey and quiz answers.

    Parameters:
        persona    (str):  e.g. "non-it", "graduate"
        edu        (str):  e.g. "graduate", "self"
        tech       (list): e.g. ["pc", "office", "excel-form"]
        strengths  (list): e.g. ["logic", "numbers", "building"]
        work_style (dict): e.g. {"da": "detail", "st": "solo"}
        goal       (str):  e.g. "job", "explore", "freelance"
        answers    (list): e.g. [2, 3, 0, 1, 2, 3, 1, 2]
                           Each answer is 0 (beginner) to 3 (expert)

    Returns:
        dict: {"ai": 82, "data": 75, "dev": 68, "cloud": 71, "cyber": 65}
    """

    # ── Step 1: Start every career with a base score of 48 ──
    # No one starts at 0 — everyone has some potential in every field!
    scores = {
        "ai":    48,
        "data":  46,
        "dev":   50,   # dev gets slightly higher base — most beginner-friendly
        "cloud": 44,
        "cyber": 44
    }

    # ── Step 2: Add points based on NATURAL STRENGTHS ───────
    # Strengths come from survey Step 3 (everyday skills, not IT skills)

    if "logic" in strengths or "numbers" in strengths:
        scores["ai"]   += 18   # logic = great for ML algorithms
        scores["data"] += 16   # numbers = great for data analysis

    if "creative" in strengths or "building" in strengths:
        scores["dev"]  += 18   # building things = developer mindset
        scores["ai"]   += 5    # creative thinking also helps AI

    if "research" in strengths:
        scores["data"] += 12   # research = data analysis
        scores["cyber"] += 10  # research = finding security vulnerabilities
        scores["ai"]   += 8    # research = understanding ML papers

    if "fixing" in strengths or "organizing" in strengths:
        scores["cloud"] += 16  # fixing things = managing infrastructure
        scores["cyber"] += 12  # organizing = incident response

    if "numbers" in strengths:
        scores["data"] += 10   # extra boost for data

    if "writing" in strengths or "talking" in strengths:
        scores["dev"] += 6     # communication = building user-friendly apps

    # ── Step 3: Add points based on WORK STYLE ─────────────
    # Work style comes from survey Step 4 (personality pairs)

    build_vs_analyze = work_style.get("ba", "")
    detail_vs_big    = work_style.get("da", "")
    solo_vs_team     = work_style.get("st", "")
    fast_vs_thorough = work_style.get("ft", "")

    if build_vs_analyze == "build":
        scores["dev"]   += 12  # builders → developers
        scores["cloud"] += 8   # builders → infrastructure

    if build_vs_analyze == "analyze":
        scores["ai"]   += 12   # analyzers → AI/ML
        scores["data"] += 12   # analyzers → data science

    if detail_vs_big == "detail":
        scores["cyber"] += 14  # detail-oriented → security analysts
        scores["data"]  += 8   # detail → data accuracy

    if solo_vs_team == "solo":
        scores["cyber"] += 6   # security work = often independent
        scores["ai"]    += 5   # ML research = deep solo thinking

    if fast_vs_thorough == "fast":
        scores["dev"] += 8     # developers ship fast and iterate

    # ── Step 4: Add points based on TECH EXPOSURE ──────────
    # Tech exposure comes from survey Step 2

    if "html" in tech or "website" in tech:
        scores["dev"] += 14    # already tried web = developer potential

    if "excel-form" in tech or "office" in tech:
        scores["data"] += 12   # spreadsheet comfort = data analyst potential

    if "python" in tech:
        scores["ai"]   += 14   # python = AI/ML pathway
        scores["data"] += 8    # python = data science pathway

    if "none" in tech:
        scores["dev"] += 8     # dev is the most beginner-friendly entry point

    # ── Step 5: Add points based on QUIZ ANSWERS ───────────
    # Each answer is 0 (beginner) to 3 (most experienced/interested)
    # We look at the question category to decide which career gets points

    # Get the question categories based on persona
    # (This mirrors the frontend logic — same 3 question sets)
    q_categories = get_question_categories(persona, tech)

    for i, answer in enumerate(answers):
        if answer is None or i >= len(q_categories):
            continue

        category = q_categories[i]
        boost = answer  # 0, 1, 2, or 3

        # Map category to career scores
        if "Data" in category or "Numbers" in category:
            scores["data"] += boost * 4
            scores["ai"]   += boost * 3

        elif "Programming" in category or "Code" in category:
            scores["dev"] += boost * 5
            scores["ai"]  += boost * 3

        elif "Cloud" in category or "Automation" in category:
            scores["cloud"] += boost * 5

        elif "Interest" in category or "Vision" in category or "Career" in category:
            # Answer 0 = dev, 1 = data, 2 = ai, 3 = cloud
            career_map = {0: "dev", 1: "data", 2: "ai", 3: "cloud"}
            chosen = career_map.get(answer, "dev")
            scores[chosen] += 14

        elif "Curiosity" in category or "Tech" in category:
            if answer >= 2:
                scores["ai"] += 10

        elif "Detail" in category or "System" in category:
            scores["cyber"] += boost * 3
            scores["cloud"] += boost * 2

        elif "Work Preference" in category or "Outcome" in category:
            outcome_map = {0: "dev", 1: "data", 2: "ai", 3: "cyber"}
            chosen = outcome_map.get(answer, "dev")
            scores[chosen] += 12

    # ── Step 6: Adjust based on GOAL ───────────────────────
    if goal == "job":
        scores["dev"]  += 8   # dev has most entry-level jobs
        scores["data"] += 5

    if goal == "freelance":
        scores["dev"] += 12   # freelance web dev is the easiest to start

    if goal == "upskill":
        scores["cloud"] += 8
        scores["ai"]    += 8

    # ── Step 7: Cap all scores between 35 and 99 ───────────
    # We don't want 0% or 100% — keeps results realistic
    for career in scores:
        scores[career] = min(99, max(35, round(scores[career])))

    return scores


# ============================================================
#   HELPER FUNCTION: get_career_details()
#
#   Takes the scores dict and returns a sorted list of careers
#   with all their details — ready to send to the frontend.
# ============================================================

def get_career_details(scores, persona):
    """
    Combine scores with career info and sort from best to worst match.

    Returns a list like:
    [
      {"key": "ai", "title": "AI/ML Engineer", "score": 85, "why": "...", ...},
      {"key": "data", "title": "Data Scientist", "score": 78, ...},
      ...
    ]
    """

    results = []

    for career_key, score in scores.items():
        # Get the career info from our dictionary at the top of this file
        info = CAREER_INFO[career_key].copy()   # .copy() so we don't modify original

        # Add the calculated score
        info["score"] = score

        # Add the personalised "why this fits you" message
        why_messages = info.get("why", {})
        info["why_text"] = why_messages.get(persona, why_messages.get("default", ""))

        results.append(info)

    # Sort by score — highest first
    results.sort(key=lambda x: x["score"], reverse=True)

    # Remove the nested "why" dict before sending (frontend doesn't need it)
    for r in results:
        r.pop("why", None)

    return results


# ============================================================
#   HELPER FUNCTION: get_question_categories()
#
#   Returns the list of question categories in order,
#   matching the frontend's 3 question sets.
#   Used in Step 5 of calculate_scores() above.
# ============================================================

def get_question_categories(persona, tech):
    """Returns the question category labels for the given persona."""

    has_tech = any(t in tech for t in ["html", "python", "website"])
    is_newbie = "none" in tech or len(tech) == 0

    # Beginner questions (for non-IT, career-gap, school students)
    beginner_cats = [
        "Daily Tech Comfort",
        "Problem Solving",
        "Learning Style",
        "Attention to Detail",
        "Numbers & Patterns",
        "Visual & Creative Thinking",
        "Tech Curiosity",
        "Work Preference"
    ]

    # IT student questions (for undergrads, graduates with some IT knowledge)
    student_cats = [
        "Programming Experience",
        "Understanding Code",
        "Data Handling",
        "Interest & Passion",
        "Technical Thinking",
        "Tools & Exposure",
        "Career Vision",
        "Self Learning"
    ]

    # Professional questions
    pro_cats = [
        "Current Role",
        "Cloud Familiarity",
        "Motivation to Grow",
        "Technical Toolkit",
        "Your Strongest Asset",
        "Future Vision",
        "Certifications & Learning",
        "Side Projects"
    ]

    # Pick the right set — mirrors the frontend logic exactly
    if persona == "professional":
        return pro_cats
    elif persona in ["non-it", "career-gap"]:
        if has_tech:
            return beginner_cats[:5] + student_cats[3:6]
        return beginner_cats
    elif persona == "career-changer":
        if has_tech:
            return beginner_cats[:3] + student_cats[2:6]
        return beginner_cats
    elif persona in ["undergraduate", "graduate"]:
        if is_newbie:
            return beginner_cats
        return student_cats
    else:
        return student_cats
