# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

- 1) Set Up Pet + Owner Profile

     The user enters basic information about the owner and pet.

- 2) Add / Edit Care Tasks

     The user creates pet care tasks such as feeding, walking, medication, grooming, enrichment, etc.

- 3) Generate Daily Care Plan

     The app sorts and selects tasks based on constraints, then creates a daily schedule.

# PawPal+ Main Objects

## Owner

**Attributes:** `name`, `available_time`, `preferences`
**Methods:** `update_profile()`, `get_availability()`

## Pet

**Attributes:** `name`, `species`, `breed`, `age`, `energy_level`
**Methods:** `update_pet_info()`, `get_pet_summary()`

## CareTask

**Attributes:** `name`, `duration`, `priority`, `category`, `required`
**Methods:** `update_task()`, `get_task_summary()`

## TaskManager

**Attributes:** `tasks`
**Methods:** `add_task()`, `edit_task()`, `delete_task()`, `get_tasks()`

## Scheduler

**Attributes:** `tasks`, `available_time`, `scheduled_tasks`, `skipped_tasks`
**Methods:** `sort_tasks()`, `generate_plan()`, `explain_plan()`

## DailyPlan

**Attributes:** `scheduled_tasks`, `skipped_tasks`, `total_time_used`
**Methods:** `display_plan()`, `show_skipped_tasks()`, `get_summary()`

# Core Actions

1. Create owner and pet profile
2. Add or edit care tasks
3. Generate and explain the daily care plan



**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

1. Owner has no Pet reference
An owner should hold their pet(s). Right now nothing connects them after creation — Scheduler and DailyPlan have no idea which pet the plan is for.


2. Scheduler never sees Pet
The pet's energy_level and species should influence scheduling (a high-energy dog needs a walk; a cat doesn't). The scheduler only sees TaskManager and Owner — it's blind to the pet.

3. DailyPlan is context-free
It stores tasks but has no date, no owner, no pet. You can't tell which day it's for or who it belongs to — makes multi-day history or display impossible.

Logic Bottlenecks
4. sort_tasks() and generate_plan() are disconnected
sort_tasks() returns a List[CareTask] but generate_plan() doesn't take that as input. Either generate_plan() will call sort_tasks() internally (hidden dependency) or it'll sort independently (double work). Make the flow explicit:

5. TaskManager.get_tasks() has no filtering
The scheduler will need to ask "give me only required tasks" or "tasks under 30 minutes" — but get_tasks() returns everything. Consider adding:

6. CareTask.priority has no enforced range or enum
priority: int with only a comment # 1 = highest is fragile. If one task is priority 1 and another is 100, the sort will work but the intent is ambiguous. An Enum or a validated range prevents bugs:

7. Owner.available_time is a single flat number
A single int (minutes/day) can't represent time-of-day constraints — morning feeding, evening medication, etc. This isn't a blocker for v1, but Scheduler will hit a wall if you ever want to order tasks by time-of-day rather than just priority.

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---
for the explain_plan() function
Performance is unchanged — both are O(n) and "\n".join() is already the right approach for building strings in Python. The gain here is purely readability.


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
