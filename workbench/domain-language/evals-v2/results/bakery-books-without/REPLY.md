Good idea to settle this now, before the names get into more code. I read the README and `src/money.py`. Your names are mostly fine. Below, each of your words sits next to what a bookkeeper would call the same thing, with the name I'd suggest we use. You don't have to talk like an accountant. It's just handy if the app's words match what your accountant or the tax forms say.

| What you call it | What a bookkeeper calls it | Suggested name |
|---|---|---|
| money log | cash book (or ledger) | **cash book** |
| a line in the log | transaction (or entry) | **transaction** |
| money in / money out | income / expense (money received / money paid) | **money in / money out**. Your words are clear, so keep them |
| pot ("ingredients", "wages", "bread sales") | category (accountants say "account", as in "chart of accounts") | **category** |
| adding up every pot at month end | profit and loss for the month (P&L) | **monthly summary** (it's your P&L) |
| what you owe the flour mill | accounts payable (a bill owed to a supplier) | **unpaid bills** |
| bank minus what you owe | net position (a very small balance sheet) | **where I stand** or **net position** |

Why I'd change two of them:

- **"Pot" → "category".** A pot sounds like a place where money sits, like a savings pot at the bank. Yours aren't that. They're labels saying where money came from or went. "Category" says that without the mix-up. I'd skip the accountant word "account", because it clashes with your bank account.
- **"Money log" → "cash book".** That's the traditional name for exactly this: a dated list of money in and out. It's also what an accountant will ask for. If you like "money log" better, keep it. The important thing is picking one name and sticking with it.

Three things I need you to tell me, because they change how the app works, not just what things are called:

1. **When you buy flour from the mill on credit, when do you write the line?** When the flour arrives, when you pay the bill, or both? If it's both, the flour cost gets counted twice in the monthly summary. If it's only when you pay, your "ingredients" total shows when you paid, not when you used the flour. Either can work. I just need to know which you do.
2. **Which way round is the sum?** You said you take what's in the bank *off* what you owe the mill. That gives a positive number when you're in trouble and a negative one when you're fine. I'm guessing you mean bank **minus** what you owe, so a positive number is good. Is that right?
3. **Is the mill the only one you owe, and does anyone owe you?** For example, a café that pays for its bread at the end of the month. If so, "where I stand" should count that too.

Once you're happy with the names, I'll write them into a short glossary file in the project and rename things in the code to match (`LogLine` → `Transaction`, `pot` → `category`, `pot_totals` → `category_totals`, and so on). I haven't changed anything yet.
