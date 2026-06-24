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
