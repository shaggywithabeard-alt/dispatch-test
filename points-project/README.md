# Points Project

A rewards-points tracker for resale customers, published as a claude.ai artifact:
https://claude.ai/artifact/YS5raHBgaqh5PHbUbWdB4v

- **Owner view** (only the artifact owner sees it): add customers (each gets a customer number starting at 1001),
  tap +10 … +100 to add points, redeem points, undo the last change, remove a customer.
- **Customer view**: anyone the artifact is shared with types their customer number or full name and sees
  their balance and recent activity.

Data lives in the artifact's shared database (`customers/<number>`), not in this file.
Only the owner can write; everyone else can only read.

To update the page, edit `index.html` and republish it to the same artifact URL.
