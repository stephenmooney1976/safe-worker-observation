# Project Title
## SwoDailyEtl

## Description
Python automation script that performs an ETL of safe worker observation data gathered from multiple sources.
Currently,configured with a python 3.9 interpreter.

## Getting Started
Steps to set up script environment and schedule execution
1. Check if host os has a native python interpreter, preferably 3.7 or greater
2. If not download one from https://www.python.org/downloads/release/python-390/
3. Clone this repo into local directory on your computer


## Installation
1. Open a command prompt (Windows) or shell (Linux)
2. cd (change directory) into project directory from command line
3. run "python -m venv venv" to create a virtual env directory within project
4. run ".\venv\Scripts\activate" (Windows) or "source ./venv/bin/activate" (Linux) to activate environment
5. run "pip install -r requirements.txt" to install necessary packages in virtual environment

## Running and Scheduling
1. From cmd or shell "python swo_etl.py"
2. To schedule use task scheduler (Windows) or cron utility (Linux).