---
name: grill-me
description: A relentless interview to sharpen a plan or design. Stateless variant — does not require a codebase or existing CONTEXT.md. Use when the user wants to stress-test a plan, idea, or design before building.
disable-model-invocation: true
---

# Grill Me

A **stateless** grilling session. Unlike `/grilling` (which inspects the codebase to answer its own questions), this skill operates purely from the user's verbal descriptions. Use this when:

- There is no codebase yet (greenfield planning)
- The user wants to validate an idea before any code exists
- The discussion is about strategy, product direction, or architecture at a whiteboard level

## Rules

1. Interview the user relentlessly about every aspect of their plan until you reach a shared understanding.
2. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one.
3. For each question, provide your recommended answer — don't just ask, also advise.
4. Ask questions **one at a time**. Wait for the user's response before continuing. Asking multiple questions at once is overwhelming.
5. Do **not** explore the codebase — there may not be one. Work entirely from what the user tells you.
6. When you identify a contradiction or gap in the plan, surface it directly: state what conflicts, why it matters, and what the options are.
7. End the session by summarising the resolved decisions and any open items that still need answers.
