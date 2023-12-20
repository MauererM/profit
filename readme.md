# PROFIT
##### Python-Based Return On Investment and Financial Investigation Tool
The core idea of PROFIT is to aggregate (personal) financial data from different sources (e.g., different banks, accounts, portfolios) in order to provide an overview of one's holistic financial situation. 

There are two core asset categories that can be tracked and analyzed by PROFIT: (Bank) accounts, and investments (like stocks). 
Assets can be grouped via user-configurable settings, and plotted accordingly (e.g., groups for savings, retirement etc.).

All data is managed locally with human-readable CSV files.

### Try it out:
1. Some example data is provided already: Simply run ```python3 profit_main.py``` in the top-level directory and look at the results in the terminal and *plots* folder. Some packages, most notably *matplotlib* or *pandas*, might require installation first.
2. You can also run it with these flags:
  ```--days <N>```, where ```<N>``` is the number of days into the past that the analysis should be performed for. 
  ```--interactive```, where PROFIT will prompt you to update missing or new data on-the-fly via the terminal.

### Features
* Data aggregation and plotting: Accounts, investments, cash etc.
    - Asset values and returns
    - Payouts and fees
    - Consideration of different asset purposes/groups (e.g., retirement, liquidity etc.)
    - Note: Debt is not (yet) supported
* Automatic gathering of market prices and foreign exchange rates
	- Data can also be provided manually
* Uses Yahoo Finance (or others; configurable via plugin/subpackage) for automatic data retrieval

All data is stored and manipulated locally, using simple text files that are human-readable. Hence, there are no privacy concerns and no complex databases. 

Two asset classes are considered: Accounts simply hold balances, whereas investments (e.g., stocks or funds) are analyzed in more detail with respect to valuation and returns. Market prices of traded securities are obtained automatically, if possible. The data can also be provided manually. The assets can be of any currency. Foreign exchange rates are also obtained automatically.

### Screenshots:
![screenshot all assets stackedplot](https://github.com/MauererM/profit/raw/master/doc/screenshots/screen_all_assets.png)
![screenshot all assets stackedplot](https://github.com/MauererM/profit/raw/master/doc/screenshots/screen_indices.png)
![screenshot all assets stackedplot](https://github.com/MauererM/profit/raw/master/doc/screenshots/screen_returns_abs.png)
![screenshot all assets stackedplot](https://github.com/MauererM/profit/raw/master/doc/screenshots/screen_values.png)
![screenshot all assets stackedplot](https://github.com/MauererM/profit/raw/master/doc/screenshots/screen_values_groups.png)


