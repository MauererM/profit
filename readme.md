# PROFIT
##### Python-Based Return On Investment and Financial Investigation Tool

### Features
* Data aggregation from different banks, accounts, investments etc.
* Long-term financial data analysis and plotting
	- Asset values and returns
	- Payouts and fees
	- Consideration of different asset purposes (e.g., retirement, liquidity etc.)
* Focus on long-term maintainability and simplicity
	- Python-based
	- Local data storage (human readable text files)
* Automatic gathering of market prices and foreign exchange rates
	- Data can also be provided manually
* MIT License

PROFIT is a simple aggregation and analysis tool for personal finance. Its key characteristics are long-term maintainability and simplicity.
All data is stored and manipulated locally, using simple text files that are human-readable for easy access and manipulation.

Two asset classes are considered: Accounts simply hold balances, whereas investments (e.g., stocks or funds), are analyzed in more detail with respect to valuation and returns.

The assets can be of any currency, as foreign exchange rates and market prices are obtained automatically. A local database of market data is automatically maintained, such that historical prices are also available offline.

### Usage
The tool comprises a set of python files that evaluate the given accounts and investments.

##### Try it out:
1. git clone "url" (or simply download the repository)
2. Run "main.py" and look at the results (Some exemplary assets are provided)
3. Modify the files in the "accounts" and "investments" folder to your liking
4. As simple as that

Data is provided and maintained as text-files that must adhere to certain formatting rules. Further information is given in the manual (doc folder)

### Contribution:

#### To Do:
- [ ] Test on Windows
- [ ] Plot some moving averages
- [ ] Plot Forex-rates
- [ ] More parsing-checks while file parsing: e.g., missing delimiters, wrong date format nonzero numbers when they should be zero etc.
- [ ] More financial data providers (e.g., with pandas-datareader), maybe with automatic fallbacks
