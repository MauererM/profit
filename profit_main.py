from profit_src import profit
from config import ProfitConfig

# Todo: How to handle the config.py? Have it on this level? Have it as class and dependecy-inject it into profit.py? How to best handle the config-data? Where to store the folder-paths?

if __name__ == '__main__':
    config = ProfitConfig()
    profit.main(config)