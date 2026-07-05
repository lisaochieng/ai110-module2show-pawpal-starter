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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
