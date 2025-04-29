import time
import functools
from datetime import datetime

# ANSI Color codes
class Colors:
    HEADER = '\033[95m'     # Pink
    BLUE = '\033[94m'       # Blue
    GREEN = '\033[92m'      # Green
    YELLOW = '\033[93m'     # Yellow
    RED = '\033[91m'        # Red
    ENDC = '\033[0m'        # End color
    BOLD = '\033[1m'        # Bold text
    UNDERLINE = '\033[4m'   # Underline text

def measure_execution_time(func):
    """
    A decorator that measures the execution time of a function.
    Prints the execution time with colored output.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(
                f"[{current_time}] Function "
                f"{Colors.BLUE}{Colors.BOLD}{func.__name__}{Colors.ENDC} "
                f"took {Colors.GREEN}{execution_time:.4f}{Colors.ENDC} seconds"
            )
            
            return result
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(
                f"[{current_time}] {Colors.RED}ERROR{Colors.ENDC} in "
                f"{Colors.BLUE}{Colors.BOLD}{func.__name__}{Colors.ENDC}: {str(e)}"
            )
            print(
                f"Failed execution took "
                f"{Colors.RED}{execution_time:.4f}{Colors.ENDC} seconds"
            )
            raise
    return wrapper

class BlockTimer:
    """
    A context manager that measures the execution time of a code block.
    Prints timing information with colored output.
    """
    def __init__(self, block_name, function_name):
        self.block_name = block_name
        self.function_name = function_name
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        execution_time = end_time - self.start_time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if exc_type is None:
            print(
                f"[{current_time}] Block "
                f"{Colors.YELLOW}{Colors.BOLD}'{self.block_name}'{Colors.ENDC} "
                f"in '{Colors.BLUE}{Colors.BOLD}{self.function_name}{Colors.ENDC}' "
                f"took {Colors.GREEN}{execution_time:.4f}{Colors.ENDC} seconds"
            )
        else:
            print(
                f"[{current_time}] {Colors.RED}ERROR{Colors.ENDC} in block "
                f"{Colors.YELLOW}{Colors.BOLD}'{self.block_name}'{Colors.ENDC} "
                f"of '{Colors.BLUE}{self.function_name}{Colors.ENDC}': {str(exc_val)}"
            )
            print(
                f"Failed execution took "
                f"{Colors.RED}{execution_time:.4f}{Colors.ENDC} seconds"
            )

def block_profiler(func):
    """
    A decorator that provides a BlockTimer for profiling code blocks.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        def create_timer(block_name):
            return BlockTimer(block_name, func.__name__)
        
        kwargs['create_timer'] = create_timer
        return func(*args, **kwargs)
    return wrapper
