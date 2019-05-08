# PROFIT
##### Python-Based Return On Investment and Financial Investigation Tool

### Features
* Data aggregation: Accounts, investments, cash etc.
* Long-term financial data analysis, tracking and plotting
	- Asset values and returns
	- Payouts and fees
	- Consideration of different asset purposes (e.g., retirement, liquidity etc.)
* Focus on long-term maintainability, scalability and simplicity
	- Python-based
	- Simple, local data storage (human readable text files): No privacy issues
* Automatic gathering of market prices and foreign exchange rates
	- Data can also be provided manually
* MIT License
* Uses the Alpha Vantage API to automatically obtain market data

PROFIT is a simple aggregation and analysis tool for personal finance. It provides a comprehensive overview of the tracked assets. This is usually complicated by the fact that assets are commonly held in different banks and accounts, with numerous currencies. Furthermore, office software, which is often used to track personal assets, scales badly, i.e., adding/removing assets requires new spreadsheets or updated formulas. PROFIT is simple and focuses on long-term maintainability, simplicity and scalability.

All data is stored and manipulated locally, using simple text files that are human-readable. Hence, there are no privacy concerns and no complex data bases. This allows the evaluation of the data also in the far future, when maybe not even Python exists anymore :speak_no_evil:.

Two asset classes are considered: Accounts simply hold balances, whereas investments (e.g., stocks or funds) are analyzed in more detail with respect to valuation and returns. Market prices of traded securities are obtained automatically, if possible. The data can also be provided manually. The assets can be of any currency. Foreign exchange rates are also obtained automatically.

### Screenshots:
Below are some of the outputs of the tool. Different PDF plots are created. Assets can be grouped for more detailed insights.
![screenshot all assets stackedplot](https://github.com/MauererM/profit/raw/master/doc/screenshots/screen_all_assets.png)
![screenshot all assets stackedplot](https://github.com/MauererM/profit/raw/master/doc/screenshots/screen_indices.png)
![screenshot all assets stackedplot](https://github.com/MauererM/profit/raw/master/doc/screenshots/screen_returns.png)
![screenshot all assets stackedplot](https://github.com/MauererM/profit/raw/master/doc/screenshots/screen_values_groups.png)
![screenshot all assets stackedplot](https://github.com/MauererM/profit/raw/master/doc/figures/Account_Example_Labelled.png)

### Try it out::
1. `git clone https://github.com/MauererM/profit.git` (or simply download the repository with the direct link).
2. (Optional) Obtain an API key from Alpha Vantage (for free, https://www.alphavantage.co/) and enter it in *setup.py*.
3. Run *PROFIT_main.py* (with a Python 3 interpreter) and look at the results in the *plots* folder (Some exemplary assets are provided). Some packages might have to be installed, most probably *alpha_vantage* and *matplotlib*.
4. Move the provided examples to the *accounts* and *investments* folders (whose content is not tracked by git) and modify them to your liking. Change the names of the target folders in *PYTHON_main.py* to use the real folders (*ACCOUNT_FOLDER* and *INVESTMENT_FOLDER* strings).
5. As simple as that :moneybag:
6. The short manual provides more information: [PROFIT manual (PDF from doc folder)](https://github.com/MauererM/profit/raw/master/doc/manual.pdf "PROFIT manual (PDF)")

### Contribution:
`git clone https://github.com/MauererM/profit.git`
