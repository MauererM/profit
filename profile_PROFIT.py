import cProfile
import subprocess
from pstats import Stats

script = "PROFIT_main.py"
METHOD = "exec"

if __name__ == "__main__":
    # Create a profiler object
    profiler = cProfile.Profile()

    if METHOD == "subprocess":

        try:
            profiler.enable()
            result = subprocess.run(['python3', script], check=True, text=True, capture_output=True)
            profiler.disable()
            output = result.stdout
            return_code = result.returncode
        except:
            print("Error")

    elif METHOD == "exec":

        try:
            profiler.enable()
            with open(script, 'r') as script_file:
                script_code = script_file.read()
                exec(script_code)
            profiler.disable()
        except:
            print(f"Error: '{script}' not found.")

    stats = Stats(profiler)
    stats.sort_stats('cumtime').print_stats(100)
######################################
# Some profiling results:

# Settings:
"""
- No market data (only forex-data provided in marketdata)
- No online provider (to be done/optimized in a 2nd step)
- 5k days into the past (which is quite a lot)
- With the 10 investments that are default in master (AAPL - RandomStock)
- The "exec" version is used (profiler output is more sensible)
"""

# Results:
"""
Baseline: 94.8s, 95.2s, 97.2s, 95.6s ==> 95.7s avg
Top slow functions (excluding matplotlib for now): 
    forex.py:168 (perform_conversion)
    forex.py:186 (listcomp)
    investment.py:396 (set_analysis_data)
"""

""" 
After introducing a dictionary for the dates in forex.py and changing its perform_conversion: 49.8s
New violators: stringoperations.py:93 (str2datetime), dateoperations.py:56 (format_datelist)
There's another section that can benefit from the dict-system of forex.py. TBD. 
Also: Further verify forex.py. 
"""

"""
After caching the str2datetime and datetime2str and using the cached system via a global analyzer-class: 33.5s
New violators: 
stringoperations.py:121 (str2datetime) (still used, especially in plotting)
dateoperations.py:56 (format_datelist)
dateoperations.py:229 (extend_data_future)
investmetn.py:set_analysis_data
dateoperations.py:listcomp (246)
"""

"""
After removing str2date from plotting and some other functions, too: 18.7, 17.9, 17.7 ==> 18.1s 
Next: Will the single-use dict in dateoperations bring a benefit?
"""

"""
After improving that single lookup in dateoperations: 15.9, 15.3, 15.7
Violators:
plotting.py:844(plot_asset_values_payout_individual)
plotting.py:970(plot_asset_returns_individaul)
plotting-aux.py:102(create_stackedplot)
"""

"""
Final conclusion: It's hard now to optimize further, most time is needed by the plotting-functions. 
Final performance: 16.3, 15.7, 15.7 ==> 15.9 (After a bugfix: 19.3s)
==> Speedup of factor 6 achieved. 
"""

"""
Now, the Yahoo Finance data provider is also enabled (API cooldown set to 0.2s). Market data is also available. 
Baseline: 65s, 68.0s 
After optimizing (dict-lookup) marketdata.py: 42.2, 41.4s
After optimizing the list-fusing: 
"""