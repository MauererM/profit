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

    #profiler.print_stats(sort="cumulative", topN=50)
    stats = Stats(profiler)
    stats.sort_stats('cumtime').print_stats(50)
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
Ideas to improve: 
- Implement its own analysis class to only calculate the reference date-list once, and store it somehow in a dict
- Get rid of the cascaded for-loops
- Check the todos in the code
"""


""" 
After introducing a dictionary for the dates in forex.py and changing its perform_conversion: 49.8s
New violators: stringoperations.py:93 (str2datetime), dateoperations.py:56 (format_datelist)
There's another "todo" that can benefit from the dict-system of forex.py. TBD. 
Also todo: Further verify forex.py. 
"""