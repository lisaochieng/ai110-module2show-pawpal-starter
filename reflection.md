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

I leaned on my AI assistant differently in each phase. Early on it was a
sounding board for the class design; later it was more of a pair-programmer for
writing methods, drafting tests, and untangling errors.

The features that helped most were the ones where it could actually see my
files. Pointing it at `pawpal_system.py` and asking targeted questions ("sort
these HH:MM strings with a lambda key," "what edge cases should I test") gave me
much better answers than vague ones. Having it run the code and tests and read
the output itself caught things I would've missed — like a Windows-only crash
where an emoji in my conflict warning couldn't print in the terminal.

Splitting the work into **separate chat sessions per phase** kept me organized.
The planning session stayed about algorithms, the implementation session about
code, and the testing session about edge cases. When a chat only holds one
kind of context, it stops drifting and its suggestions stay on-topic.

**b. Judgment and verification**

I didn't take everything the AI offered. When we looked at `detect_conflicts`,
it suggested a shorter `defaultdict` + comprehension version. It was more
"Pythonic," but harder to read at a glance, so I kept my explicit loop — same
O(n) speed, easier for a human to follow. Keeping the design clean mattered
more to me than saving three lines.

I verified suggestions by running them, not by trusting them. Every method got
exercised in `main.py` and then locked in with tests (`python -m pytest`), and
for the date math I used fixed dates so I could check the rollovers (Jul 31 →
Aug 1) myself instead of assuming they were right.

---

## 4. Testing and Verification

**a. What you tested**

I wrote 26 tests covering all four scheduling behaviors: sorting (chronological
order, untimed tasks last, empty list, no mutation), filtering (by pet, by
status, combined), recurrence (daily/weekly, non-recurring returns nothing, and
month/year rollovers), and conflict detection (same-time clashes, no false
positives, untimed tasks ignored). I also tested the plain planner — an empty
pet and the low-priority task getting skipped when time runs out.

These mattered because the recurrence and conflict logic are the parts most
likely to break quietly. A wrong date or a missed clash wouldn't crash the app,
it would just give the owner a bad plan, so I wanted tests watching for exactly
that.

**b. Confidence**

Fairly confident — 4 out of 5. All 26 tests pass and they cover the tricky edge
cases, so I trust the backend logic. I held back the last point because
conflict detection only catches exact time matches, not overlapping durations,
and I haven't written any tests for the Streamlit UI in `app.py` yet.

If I had more time I'd test overlapping-duration conflicts (a 30-min walk at
08:00 vs a feeding at 08:15) and add a couple of smoke tests for the app.

---

## 5. Reflection

**a. What went well**

I'm most happy with the recurrence feature. Figuring out that the date math
belonged on `Task` but the "add it to the list" part belonged on `Pet` felt
like a real design decision, and it worked cleanly once I split it that way.

**b. What you would improve**

I'd upgrade conflict detection to compare actual time ranges instead of just
exact matches, and I'd give tasks a proper date/time type instead of a plain
`"HH:MM"` string so I'm not relying on string sorting.

**c. Key takeaway**

Working with AI is fastest when I stay in charge of the design. It's great at
producing options and catching bugs, but I got the best results when I decided
*what* I wanted, gave it the files, and then checked its work by running it —
not when I let it decide the structure for me.
