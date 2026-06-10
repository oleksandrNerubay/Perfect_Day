---
description: Research any topic and save a structured markdown report to reports/
argument-hint: <topic>
allowed-tools: WebSearch, WebFetch, Read, Grep, Write, Bash(date:*), Bash(mkdir:*)
disable-model-invocation: true
---

You are conducting a structured research session on: **$ARGUMENTS**

Before doing any research, you must gather three pieces of information from the user. Ask them one at a time, waiting for an answer before moving to the next question.

## Step 1 — Clarifying Questions

**Question 1 — Scope:**
Ask the user: "How broad or deep should this research go? Choose one: (a) quick overview — 3–5 key points, (b) standard briefing — balanced depth and breadth, or (c) full deep-dive — exhaustive coverage with nuance and trade-offs."

Wait for the user's answer before asking Question 2.

**Question 2 — Audience:**
Ask the user: "Who is the primary audience for this report? For example: technical engineers, executive / business leadership, general public, or a mixed audience?"

Wait for the user's answer before asking Question 3.

**Question 3 — Focus Areas:**
Ask the user: "Are there specific angles or sub-topics you want prioritized? For example: competitive landscape, technical implementation details, regulatory considerations, market trends, or relevance to the Perfect Day platform. List as many as you like, or say 'no preference' to let me decide."

Wait for the user's answer. Once you have all three answers, proceed to Step 2.

---

## Step 2 — Research Execution

Execute ALL four source types below. Tailor depth and angle to the scope and audience answers you collected.

### Source A — Local Codebase (if applicable)
If the topic plausibly relates to this project (event planning, vendor management, AI recommendations, voice input, Flask, MongoDB, React, California market, deal discovery, user engagement), scan the codebase:
- Use Grep to search for relevant terms in `/home/sanix/Documents/perfectDay`
- Use Read to read any relevant files found
- Note what the current implementation does or does not cover regarding this topic

If the topic is entirely unrelated to the codebase, skip this source and note that in the report.

### Source B — Training Knowledge
Draw on your own knowledge to establish the foundational landscape: definitions, history, key players, established best practices, and known trade-offs as of your training cutoff. Flag anything time-sensitive as "verify with live sources."

### Source C — WebSearch
Perform 2–3 targeted web searches to find:
- Recent developments (past 12–18 months)
- Authoritative primary sources (official docs, academic papers, industry reports)
- Practitioner perspectives (technical blogs, case studies)

Collect the most relevant URLs from results.

### Source D — WebFetch
Fetch and read the full content of the 3–5 highest-quality URLs found in Source C. Prioritize primary sources over secondary, and recent content over older.

---

## Step 3 — Filename Construction

1. Take the topic from $ARGUMENTS
2. Convert to lowercase, replace spaces and special characters with hyphens, collapse consecutive hyphens
3. Get today's date: !`date +%Y-%m-%d`
4. Final path: `reports/<slug>-<date>.md`
5. Ensure the directory exists: !`mkdir -p /home/sanix/Documents/perfectDay/reports`

Example: topic "React state management" → `reports/react-state-management-2026-06-07.md`

---

## Step 4 — Write the Report

Write the completed report to the path constructed above using the Write tool. Use this exact structure:

```
# Research Report: [Topic Title]

**Date:** [YYYY-MM-DD]
**Scope:** [Answer from Question 1]
**Audience:** [Answer from Question 2]
**Focus Areas:** [Answer from Question 3]
**Sources Used:** Training knowledge, WebSearch, WebFetch ([N] pages fetched)[, local codebase]

---

## Executive Summary

[3–5 sentences. Lead with the "so what" — the single most important takeaway for this audience. Plain language unless audience is technical.]

---

## Key Findings

[5–8 bullet points. Each is one concrete, specific, actionable fact. Include a source attribution in parentheses where possible.]

---

## Deep Dive

### [Section 1: First Major Theme]

[2–4 paragraphs. Evidence-driven. Cite sources inline. Note where sources conflict or data is uncertain.]

### [Section 2: Second Major Theme]

[2–4 paragraphs.]

### [Additional sections as needed based on scope and focus areas]

---

## What This Means for Perfect Day

[3–5 bullet points or paragraphs connecting findings to the Perfect Day platform — its user base (consumers + vendors), California market, tech stack (React + Flask + MongoDB), and business model (AI recommendations, one-click planning, deal discovery). If the topic is genuinely unrelated, say so clearly and note any indirect relevance.]

---

## Sources

### Web Sources
[Numbered list — Title, URL, publication date or date accessed]

### Codebase References
[Files read, or "Not applicable."]

### Training Knowledge Notes
[Flag any significant claims drawn solely from training knowledge, noting the August 2025 cutoff as a limitation for time-sensitive assertions.]

---

## Research Notes

**Confidence level:** [High / Medium / Low] — brief rationale
**Key uncertainties:** [What could not be confirmed]
**Suggested follow-up:** [1–3 specific next questions worth investigating]
```

---

## Step 5 — Confirm to User

After writing the file, tell the user:
- The exact file path where the report was saved
- How many web sources were fetched
- Any significant gaps or low-confidence areas to be aware of
- One suggested follow-up research question
