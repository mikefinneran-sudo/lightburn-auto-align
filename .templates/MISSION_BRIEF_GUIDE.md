# Mission Brief System - User Guide

## Why Mission Briefs 10x Your Efficiency

**The Problem:**
Most Claude sessions start like this:
```
You: "Build an API"
Claude: "What kind of API?"
You: "REST API"
Claude: "What endpoints?"
You: "User management"
Claude: "What database?"
You: "You choose"
Claude: "What about authentication?"
[10 messages later, finally starting to code]
```

**Time wasted: 10-15 minutes**

**The Solution:**
With a mission brief:
```
You: "Build REST API. See MISSION_BRIEF.md"
Claude: [reads brief, starts coding immediately]
```

**Time wasted: 0 minutes**

---

## How to Use Mission Briefs

### Step 1: Choose Template

```bash
# For new projects
cp .templates/MISSION_BRIEF_TEMPLATE.md MISSION_BRIEF.md

# Or use pre-made templates
cp .templates/examples/api-speedrun.md MISSION_BRIEF.md
```

### Step 2: Fill It Out (5 minutes)

**Focus on these key sections:**

1. **Goal** - One sentence, crystal clear
2. **Success Criteria** - Specific, measurable
3. **Decision Authority** - What can Claude decide vs. what to ask about
4. **Kickoff Prompt** - Pre-written prompt to paste into Claude

**Pro tip:** The time you spend on the brief is directly subtracted from Claude's question time.

### Step 3: Start Session

**Just paste the kickoff prompt:**
```
Build REST API for user management.

GOAL: Complete CRUD API with auth in 30 minutes

REQUIREMENTS:
- 5 endpoints (GET, POST, PUT, DELETE, LIST users)
- JWT authentication
- PostgreSQL database
- 80%+ test coverage
- OpenAPI documentation

CONSTRAINTS:
- Use FastAPI (Python)
- Must integrate with existing auth service
- No new paid dependencies

DECISION AUTHORITY:
- Full autonomy on: code structure, test approach, validation logic
- Ask before: database schema design, breaking auth API changes

DELIVERABLES:
- API server code
- Test suite
- README with examples
- Docker deployment

CONTEXT: See MISSION_BRIEF.md for details.

Target: 30 min, 9/10 efficiency.

GO!
```

**Result:** Claude starts coding immediately with perfect context.

---

## The Efficiency Formula

### Traditional Approach
```
Planning with Claude:     10 min
Clarifications:           10 min
Coding:                   40 min
Misunderstandings/redo:   20 min
─────────────────────────────────
Total:                    80 min
Output:                   Medium quality
```

### Mission Brief Approach
```
Writing brief alone:       5 min
Pasting prompt:           <1 min
Claude coding:            30 min
Zero clarifications:       0 min
Zero redo:                0 min
─────────────────────────────────
Total:                    35 min
Output:                   High quality
```

**Efficiency gain: 2.3x faster + better quality**

---

## Key Sections Explained

### 1. Goal (Most Important!)

❌ **Bad:**
```
Build a web application
```

✓ **Good:**
```
Build a real-time chat application that supports 1000+ concurrent users
with <100ms message latency
```

**Why:** Specific, measurable, clear success definition.

### 2. Decision Authority (Time Saver!)

❌ **Bad:**
```
Ask me about everything
```

✓ **Good:**
```
Full autonomy: UI framework, state management, styling, test framework
Ask before: Database choice, third-party APIs, deployment platform
```

**Why:** Eliminates 90% of "should I use X or Y?" questions.

### 3. Success Criteria (Quality Gate!)

❌ **Bad:**
```
Make it work
```

✓ **Good:**
```
- All 5 endpoints respond in <100ms
- 90%+ test coverage
- Handles 1000 concurrent connections
- Complete OpenAPI documentation
- Zero linting errors
```

**Why:** Clear quality bar, prevents "good enough" syndrome.

### 4. Kickoff Prompt (Efficiency Hack!)

**Pre-write the prompt you'll paste to Claude.**

Benefits:
- No fumbling for words when you start
- Ensures you include all context
- Can be reused/templated
- Sets the right tone (urgent, autonomous)

---

## Mission Brief Templates

### Template Library

**We provide pre-made briefs for:**

1. **api-speedrun.md** - REST API in 30 minutes
2. **fullstack-sprint.md** - Complete app in 60 minutes
3. **bug-hunt.md** - Fix maximum bugs in session
4. **refactor-mission.md** - Clean up legacy code
5. **feature-add.md** - Add feature to existing codebase
6. **data-pipeline.md** - ETL/data processing
7. **cli-tool.md** - Command-line utility
8. **dashboard.md** - Analytics/monitoring dashboard

### Using Templates

```bash
# List available templates
ls .templates/examples/

# Use a template
cp .templates/examples/api-speedrun.md MISSION_BRIEF.md

# Customize for your project
vim MISSION_BRIEF.md

# Start!
# [Paste kickoff prompt into Claude Code]
```

---

## Advanced Techniques

### 1. Multi-Project Brief

For related projects:

```markdown
# Mission Brief: E-commerce Platform (3 Projects)

## Project 1: API (Day 1, 45 min)
[Full API spec]

## Project 2: Frontend (Day 2, 60 min)
[Full UI spec, references API from Project 1]

## Project 3: Admin Dashboard (Day 3, 45 min)
[Admin spec, references API and uses similar UI patterns]
```

**Benefit:** Claude remembers context between projects.

### 2. Iterative Brief

For uncertain projects:

```markdown
# Mission Brief: ML Model Optimization

## Phase 1: Baseline (30 min)
[Get working model with basic approach]

## Phase 2: Analysis (20 min)
[Profile performance, identify bottlenecks]

## Phase 3: Optimization (40 min)
[Implement improvements based on Phase 2 findings]
```

**Benefit:** Adapt based on learnings.

### 3. Parallel Brief

For independent tasks:

```markdown
# Mission Brief: System Setup

## Task A: Database Setup (Claude decides priority)
[Database configuration spec]

## Task B: API Scaffolding (Can work in parallel with A)
[API structure spec]

## Task C: Authentication (Depends on A and B)
[Auth integration spec]
```

**Benefit:** Claude can parallelize where possible.

---

## Common Mistakes

### ❌ Mistake 1: Too Vague

```markdown
Goal: Build something cool
Requirements: Make it good
```

**Fix:** Be specific. What does "cool" mean? What metrics define "good"?

### ❌ Mistake 2: Too Prescriptive

```markdown
1. First, create file api.py
2. Then, import Flask
3. Then, write route handler
4. Then, add validation
[100 more micro-steps...]
```

**Fix:** Define WHAT, not HOW. Let Claude figure out implementation.

### ❌ Mistake 3: No Decision Boundaries

```markdown
[No mention of what Claude can decide]
```

**Result:** Claude asks about every little thing.

**Fix:** Explicitly state autonomy boundaries.

### ❌ Mistake 4: Missing Context

```markdown
Goal: Add feature X to the system
[No mention of what "the system" is]
```

**Fix:** Include architecture notes, link to docs, attach key files.

### ❌ Mistake 5: Unrealistic Scope

```markdown
Goal: Build complete ERP system in 30 minutes
```

**Fix:** Right-size the scope. Complex projects need breaking down.

---

## Benchmarks

### How Long Should It Take?

**Writing your first brief:** 15-20 minutes
**After 5 briefs:** 5-10 minutes
**Using templates:** 2-5 minutes
**For repeat project types:** <2 minutes (reuse old brief)

### ROI Calculation

```
Time spent writing brief:         5 min
Time saved on clarifications:    10 min
Time saved on rework:            15 min
Quality improvement:             (priceless)
───────────────────────────────────────────
Net time saved per project:      20 min
Net quality improvement:         +15-20%
```

**After 10 projects:** You've saved 200 minutes (3.3 hours)

---

## Integration with Other Tools

### With Mission Control CLI (future)

```bash
# Auto-generate brief from template
cmc brief create --template api-speedrun

# Start session with brief
cmc session start --brief MISSION_BRIEF.md

# Brief gets auto-attached to Claude context
```

### With GitHub

```bash
# Store briefs with code
git add MISSION_BRIEF.md
git commit -m "Add mission brief for API project"

# Reference in PRs
"Implementation per MISSION_BRIEF.md specifications"
```

### With Documentation

```markdown
# README.md

## Development

This project was built following the mission brief methodology.
See MISSION_BRIEF.md for original specifications and constraints.
```

---

## Examples in Action

### Example 1: Laser Aligner Project (Our Baseline)

**What we did (no formal brief):**
```
You: "Complete the project, let me know if you need anything"
Result: 9.3/10 efficiency, but some ambiguity
```

**What we could have done with a brief:**
```
You: "See MISSION_BRIEF.md"
Brief includes:
- Exact technical approach (ArUco markers + homography)
- All 10 tasks listed
- Decision boundaries clear
- Deliverables specified

Result: Likely 9.7/10 efficiency, zero ambiguity
```

### Example 2: Speed Run API (Future)

**With brief:**
```
Time: 28 minutes (target: 30)
Quality: 95% test coverage
Efficiency: 9.5/10

Why it worked:
- Clear scope (5 endpoints, defined)
- Tech stack decided (FastAPI)
- Autonomy given (implementation details)
- Quality gate set (90% coverage)
```

---

## Checklist: Is Your Brief Good Enough?

Before starting, verify:

✓ **Goal is one clear sentence**
✓ **Success criteria are measurable**
✓ **Technology stack is specified or delegated**
✓ **Decision authority is explicit**
✓ **Scope is realistic for time available**
✓ **Deliverables are listed**
✓ **Kickoff prompt is written**
✓ **Context is attached or explained**

If all ✓, you're ready for maximum efficiency!

---

## Next Level: Brief Library

**Build your personal library:**

```
.templates/
├── my-briefs/
│   ├── python-api.md        (reused 5x)
│   ├── react-app.md         (reused 3x)
│   ├── data-pipeline.md     (reused 4x)
│   └── refactor.md          (reused 2x)
```

**Result:**
- Project #1: 15 min to write brief
- Project #10: 2 min (copy + tweak)
- Project #20: 1 min (barely customize)

**Compound efficiency gains!**

---

## The Bottom Line

**Mission Briefs are your efficiency multiplier.**

Without: 8/10 avg efficiency
With: 9.5/10 avg efficiency

**That's the difference between good and legendary.**

Start every project with a mission brief.
Your future self (and Claude) will thank you.

---

**Next:** See `.templates/examples/` for ready-to-use briefs!

