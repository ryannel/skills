# Glossary

These are the only terms the docs use. Each one means exactly one thing.

## How the terms fit together

There are two kinds of term: places a parcel can be, and stages a parcel goes through.

**Places.** A bank contains lockers. A locker holds a parcel.

```
bank  (a wall of lockers)
 └── locker  (one compartment with one door)
      └── parcel
```

**Stages.** A drop puts a parcel into a locker. From then on the parcel is waiting, and it ends up either collected or overdue.

```
drop ──> waiting ──> collected     (the customer took it)
            │
            └──────> overdue       (72 hours passed and nobody took it)
```

## Places

| Term | Meaning |
|---|---|
| **locker** | One compartment with one door. |
| **bank** | A wall of lockers. |

## Stages of a parcel

| Term | Meaning | Value stored in the code and data |
|---|---|---|
| **drop** | The courier puts a parcel into a locker and shuts the door. | (the `drop` function) |
| **waiting** | The parcel is in a locker and the customer has not taken it yet. | `claimed` |
| **collected** | The customer has taken the parcel. | `collected` |
| **overdue** | The parcel was still waiting after 72 hours. The bank flags it. | `stale` |

## Other terms

| Term | Meaning |
|---|---|
| **pickup code** | The code the customer gets once their parcel is waiting. |

## Words the code uses differently

The code and stored data have not been renamed, so two of their state values differ from the docs:

- `claimed` in the code means **waiting**. It does not mean the customer has the parcel.
- `stale` in the code means **overdue**.

## Retired words

Do not use these in the docs. They appear in older text and in one code comment.

| Retired word | Use instead |
|---|---|
| unit, hopper, door (for the compartment) | locker |
| cabinet | bank |
| claimed | waiting |
| unclaimed | waiting (or overdue, once 72 hours have passed) |
| stale | overdue |
| code (on its own) | pickup code |
