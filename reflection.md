# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

The three main things a user can do in PawPal+:

1. Add a pet (name, species/breed) so the app knows who the plan is for.
2. Add care tasks for that pet, each with a duration and priority (walk, feeding, meds, etc.).
3. Generate and view today's plan, which orders the tasks by priority and available time.

**a. Initial design**

I went with four classes:

- **Owner** — the person using the app. Holds their name, daily time budget (`available_minutes`), and their list of pets. Responsible for adding pets.
- **Pet** — the animal being cared for. Holds name, species/breed, and its own list of tasks. Responsible for adding and removing its tasks.
- **Task** — one care activity (walk, feeding, meds, etc.). Holds a name, duration, priority, and optional preferred time / recurrence. Knows whether it recurs.
- **Scheduler** — the brains. Takes a pet and the time budget and produces the ordered daily plan, and can explain how it ordered things.

I used dataclasses for Owner, Pet, and Task since they're mostly data holders, and kept Scheduler a regular class because it does the real work.

**b. Design changes**

After reviewing the skeleton I made one change to the Scheduler. Originally `explain()` took no arguments and the Scheduler kept no state, so once `generate_plan()` returned there was nothing left to explain. I added `last_plan` and `last_skipped` attributes that `generate_plan()` records, so `explain()` can describe both what got scheduled and what got dropped for lack of time. This also matches the scenario's "skip tasks if time runs out" behavior, since skipped tasks are now tracked instead of silently disappearing.

A second review pointed out that `priority` is stored as a free-form string, so sorting by it directly would order tasks alphabetically ("high", "low", "medium") instead of by importance. I added a `PRIORITY_ORDER` mapping and a `Task.priority_rank()` helper so the scheduler has a well-defined value to sort on. I made the ranking explicit in the design rather than leaving it as a hidden assumption in the scheduling code.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints, in this order of influence:

1. **Priority** (`Task.priority_rank()` via the `PRIORITY_ORDER` map) — high tasks are placed before medium and low.
2. **Available time** (`Owner.available_minutes`) — `generate_plan()` greedily packs tasks until the budget runs out and records anything that doesn't fit in `last_skipped` rather than dropping it silently.
3. **Preferred time** (`preferred_time`, "HH:MM") — used for chronological ordering (`sort_by_time()`) and for spotting clashes (`detect_conflicts()`).

Priority mattered most because the scenario is about a *busy* owner: when there isn't enough time for everything, the important tasks (meds, feeding) should survive and the optional ones (grooming) should be the ones skipped.

**b. Tradeoffs**

**Conflict detection only checks for *exact* time matches, not overlapping durations.** `detect_conflicts()` groups tasks by their exact `"HH:MM"` `preferred_time` and warns when two share a slot. It does **not** notice that a 30-minute walk at 08:00 overlaps a feeding at 08:15 — only two tasks both stamped `08:00` are flagged.

This tradeoff is reasonable here because:

- **It's lightweight and never crashes.** It returns a plain list of warning strings (empty when clean), so the UI can surface a gentle "heads up" without interval math or error handling.
- **The data doesn't justify more.** Most tasks are entered on round times (08:00, 09:00), so exact-match catches the realistic collisions a pet owner actually creates.
- **It degrades safely.** A missed overlap just means one un-warned clash — the plan is still produced and the owner can eyeball the times. Pretending to enforce a hard constraint we don't actually check would be worse than an honest, simple one.

If the app grew (vet visits, precise time blocks), the natural next step is to parse `preferred_time` into minutes and compare `[start, start + duration)` intervals — but that adds parsing and edge cases (e.g. midnight rollover) the current scenario doesn't need.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
