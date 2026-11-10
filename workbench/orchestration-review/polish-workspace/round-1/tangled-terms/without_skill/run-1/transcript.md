# tangled-terms, without skill

## Owner

can we sort out the language in this project? there are a ton of terms floating around in the docs and I'm not sure what they all mean anymore

## Agent

The project is only three files, so I read all of it. There are nine terms for about six things, and one of them contradicts itself. I haven't changed anything yet.

| Thing | Terms in use | Suggested term |
|---|---|---|
| One compartment with a door | unit, locker, hopper, door | **locker** (already used in the code and data) |
| A wall of compartments | bank, cabinet | **bank** |
| Courier puts the parcel in | drop, "scans in" | **drop** |
| Parcel is inside, waiting for the customer | claimed | **waiting** |
| Customer took the parcel | collected | **collected** |
| Not collected after 72h | stale, "unclaimed" | **stale** |
| What the customer gets | code | **pickup code** |

- **"Claimed" contradicts itself.** `docs/overview.md` says a parcel is claimed once the door shuts, then says unclaimed parcels go stale after 72h. In the code, `claimed` means "deposited, waiting", so the second sentence really means "uncollected". I'd rename the state, because "claimed" reads as "the customer has it".
- **"Hopper" is only defined by a docstring.** `src/parcel.py` says "the hopper (the locker)", and the overview says "a unit is one door". I'm reading all three as the same thing.

Questions for you:
1. Is a hopper really just a locker, or is it something distinct, such as an intake chute?
2. What does "scans in" mean: the courier badging in, or scanning the parcel's barcode?
3. Who does the bank flag stale parcels to, and does the 72h run from when the door shuts?
4. Are you happy with renaming the `claimed` state to `waiting`? It changes the stored value in `data/parcels.json`, so it is the one edit that goes beyond wording.

Once you confirm, I'll add a `docs/glossary.md`, rewrite the overview to use only those terms, and fix the docstring, plus the state rename if you want it.

## Owner

I don't know what a hopper is, I only know locker. I don't mind about "scans in" or who gets the stale flag or when the 72h starts. Please don't rename anything in the code or stored data for now, just the docs. "Stale" isn't very clear to me, so can we pick a more understandable term? I also still can't tell how these terms fit together.

## Agent

The docs now use one term per thing, and "stale" is now **overdue**. Only the docs changed; the code and stored data are untouched.

The terms fall into two groups:

**Places.** A bank contains lockers, and a locker holds a parcel.

```
bank  (a wall of lockers)
 └── locker  (one compartment with one door)
      └── parcel
```

**Stages of a parcel.** A drop puts a parcel into a locker. From then on it is waiting, and it ends up either collected or overdue.

```
drop ──> waiting ──> collected     (the customer took it)
            │
            └──────> overdue       (72 hours passed and nobody took it)
```

The only other term is **pickup code**, which is what the customer gets once their parcel is waiting.

- **Docs and code now differ on two words.** The docs say "waiting" and "overdue", while the code and data still store `claimed` and `stale`. The glossary has a mapping table so nobody has to guess.
- **"Hopper" is gone from the docs but not the code.** It still appears in the docstring in `src/parcel.py`, which I left alone as you asked. The glossary lists it as a retired word meaning locker.
- **Unit, cabinet, "unclaimed" and bare "code" are retired too.** The glossary says what to use instead of each.

I rewrote `docs/overview.md` as three short steps using only these terms, and added `docs/glossary.md` with the definitions, both diagrams and the mapping to the code values. Nothing is committed.

## Owner

That makes sense now, and "overdue" works for me. Looks good.

## Agent

Good. The two doc files are edited but not committed, so say the word if you'd like me to commit them.

If you later want the code to match the docs, the remaining differences are the `claimed` and `stale` state values and the "hopper" docstring in `src/parcel.py`.

---

Ended: the agent finished and asked nothing.
