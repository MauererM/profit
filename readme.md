# PROFIT
##### Python-Based Return On Investment and Financial Investigation Tool
The core idea of PROFIT is to aggregate financial data from different sources (e.g., different banks, accounts, portfolios) in order to provide an overview of one's holistic financial situation. 
### Features
* Data aggregation: Accounts, investments, cash etc.
* Long-term financial data analysis, tracking and plotting
    - Asset values and returns
    - Payouts and fees
    - Consideration of different asset purposes (e.g., retirement, liquidity etc.)
    - Note: Debt is not (yet) supported
* Automatic gathering of market prices and foreign exchange rates
	- Data can also be provided manually
* MIT License
* Uses Yahoo Finance (or others; configurable via plugin/subpackage) for automatic data retrieval

All data is stored and manipulated locally, using simple text files that are human-readable. Hence, there are no privacy concerns and no complex databases. 

Two asset classes are considered: Accounts simply hold balances, whereas investments (e.g., stocks or funds) are analyzed in more detail with respect to valuation and returns. Market prices of traded securities are obtained automatically, if possible. The data can also be provided manually. The assets can be of any currency. Foreign exchange rates are also obtained automatically.

### Screenshots:
Below are some of the outputs of the tool. Different PDF plots are created. Assets can be grouped for more detailed insights.
![screenshot all assets stackedplot](https://github.com/MauererM/profit/raw/master/doc/screenshots/screen_all_assets.png)
![screenshot all assets stackedplot](https://github.com/MauererM/profit/raw/master/doc/screenshots/screen_indices.png)
![screenshot all assets stackedplot](https://github.com/MauererM/profit/raw/master/doc/screenshots/screen_returns.png)
![screenshot all assets stackedplot](https://github.com/MauererM/profit/raw/master/doc/screenshots/screen_values_groups.png)
![screenshot all assets stackedplot](https://github.com/MauererM/profit/raw/master/doc/figures/Account_Example_Labelled.png)

### Try it out::
1. Run *profit_main.py* (with a Python 3 interpreter) and look at the results in the *plots* folder (Some exemplary assets are provided). Some packages might have to be installed.

