---
name: grill-with-docs
description: A relentless interview to sharpen a plan or design, which also creates ADRs and glossary entries as decisions are made. Use when the user wants to stress-test a plan and simultaneously build domain documentation.
disable-model-invocation: true
---

# Grill With Docs

A grilling session that **simultaneously produces documentation artifacts**. This skill combines two disciplines:

- **Grilling** — relentless interview to resolve design decisions (from `/grilling`)
- **Domain modeling** — capturing resolved terms and decisions into `CONTEXT.md` and ADRs (from `/domain-modeling`)

## Coordination Rules

1. Run the grilling session following all rules from the `/grilling` skill: one question at a time, provide recommended answers, walk the design tree, explore the codebase when it can answer a question.

2. **After each resolved decision**, immediately determine whether it produces:
   - A **glossary term** → update `CONTEXT.md` inline (using the format from `/domain-modeling`). Do not batch these — write them the moment a term is resolved.
   - An **architectural decision** → create an ADR in `docs/adr/` only when all three criteria are met: (a) hard to reverse, (b) surprising without context, (c) the result of a real trade-off. Use the ADR format from `/domain-modeling`.

3. If `CONTEXT.md` does not exist, create it when the first term is resolved. If `docs/adr/` does not exist, create it when the first ADR is needed.

4. Do **not** pause the grilling flow to discuss documentation mechanics. Writing docs is a side effect of resolved decisions, not a separate phase.

5. When the user uses a term that conflicts with an existing entry in `CONTEXT.md`, call it out immediately and resolve the conflict before moving on.

6. At the end of the session, summarise:
   - Resolved design decisions (with links to any ADRs created)
   - New or updated glossary terms in `CONTEXT.md`
   - Open items that still need answers
