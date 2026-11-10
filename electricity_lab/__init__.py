"""Simulated hourly electricity readings for SQL learning."""
import sys
for _stream in (sys.stdout,sys.stderr):
    if hasattr(_stream,'reconfigure'):_stream.reconfigure(encoding='utf-8',errors='backslashreplace')
__version__='1.0.0'
