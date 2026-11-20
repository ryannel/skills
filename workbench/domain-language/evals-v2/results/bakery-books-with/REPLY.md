Yes, let's settle the names now, before more gets built on them. You already walked me through how it works, which is what I needed. I've also read the README and `src/money.py`.

Almost everything you described already has a name in bookkeeping. Using those names means an accountant, or any bookkeeping app you move to later, will understand the app straight away, and you'll learn the words as we go. Here's what I'd recommend. A "yes" to each one accepts it, and you can keep any of your own words if you prefer them.

**1. A line in the money log → a Transaction.** That's the word QuickBooks, Xero and bookkeeping guides use for any money that moves: a date, an amount, in or out, and what it was for. Call it a Transaction?

**2. The money log → the Cash Book.** Keeping one book with a line for each money movement is called single-entry bookkeeping, and that book is the cash book. (You may also hear "ledger", but that word belongs to the fuller double-entry system.) Call it the Cash Book?

**3. A pot → a Category.** QuickBooks calls these categories when you file a transaction. Accountants call them *accounts*, and the full list the *chart of accounts*. I'd go with Category here, because "account" would get mixed up with your bank account in this same app. Call them Categories?

**4. In / out → Money In and Money Out.** These are your own words, and they're also the plain words Xero and most banks use, so I'd keep them. (A traditional cash book says "receipts" and "payments", but "receipt" already means the slip you get in a shop.)

**5. Adding up every pot at month end → the Profit and Loss.** This is the standard monthly report for a small business, also called the P&L or income statement. It totals each category for the month and then shows the bottom line, whether you made or lost money. Call it the Profit and Loss?

**6. What you owe the flour mill → Accounts Payable,** money owed to a **Supplier** for things you've received but not yet paid for. These are the standard terms in QuickBooks, Xero and Sage. Use them?

**7. What's in the bank → the Bank Balance.** This one needs no explaining.

Two things I need to ask rather than suggest:

**A. "Where I stand".** What do you call that figure, in your own words? Also, which way round is the subtraction: the bank balance minus what you owe the mill, or what you owe minus the bank balance? You said "take what's in the bank off what I owe", which literally means the second, but I suspect you mean the first. The app doesn't work this figure out yet either. Right now it only does the pot totals.

**B. Flour on credit.** Say the mill delivers 200 worth of flour on 28 March and you pay them on 5 April. Does that 200 count in March's Ingredients, when the flour arrived, or in April's, when the money left the bank? Both are normal ways to keep books, but the answer changes what a Transaction is and what the monthly Profit and Loss means.

Here's how the whole thing reads with those names, so you can see whether they sit right:

1. You buy flour or sell bread.
2. You add a Transaction to the Cash Book with the date, the amount, Money In or Money Out, and a Category such as Ingredients, Wages or Bread Sales.
3. At the end of the month, the app produces the Profit and Loss, with each Category's total for the month and what the bakery made or lost overall.
4. You check your Bank Balance against your Accounts Payable to the flour mill (your Supplier) to see where you stand. (The name is waiting on question A.)

I've written all of these into a new `GLOSSARY.md` in the project. Each entry is marked "Proposed" until you agree it, and the two questions above are listed at the bottom. I haven't renamed anything in the code. `LogLine`, `MoneyLog` and `pot` stay as they are, and the glossary notes which name each one is stored under, so nothing breaks. Once you've agreed the names, I'll update the README to use them. The project doesn't have an agent instructions file such as `AGENTS.md` or `CLAUDE.md` yet. That's where a short note pointing to the glossary would go, so later sessions use these names, and I can add one if you'd like.
