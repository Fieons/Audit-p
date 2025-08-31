# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a data audit and cleaning project with a structured directory organization for processing CSV files. The project focuses on data transformation from raw information to cleaned, structured relational data tables.

## Directory Structure

- `information/` - Raw, unprocessed data files (CSV format)
  - `Fin/` - Financial data files
  - `Pur/` - Purchase data files
- `cleaning/` - Python data cleaning scripts using pandas
- `format-data/` - Cleaned, structured CSV output files
- `operation/` - Operational scripts or workflows (currently empty)

## Development Commands

Since this is a Python-based data processing project, common commands include:

```bash
# Activate the virtual environment befor run the python script(if requirements.txt and virtual environment exists)
source venv/bin/activate

# Run Python scripts for data cleaning
python cleaning/script_name.py

# Check Python syntax and style
pylint cleaning/*.py
flake8 cleaning/*.py

# Run data validation on cleaned files
python -c "import pandas as pd; pd.read_csv('format-data/file.csv').info()"
```

## Data Processing Workflow

1. **Raw Data**: Store in `information/` directory
2. **Cleaning Scripts**: Create pandas-based scripts in `cleaning/` directory
3. **Processed Data**: Output cleaned CSV files to `format-data/` directory
4. **Documentation**: Maintain schema documentation in `format-data/Readme.md`

## Key Requirements

- Use pandas library for data manipulation
- Create efficient, reliable, reusable relational data tables
- Maintain documentation of data table schemas and characteristics
- Check for existing scripts and data before creating new ones
- Ensure data quality and consistency across processing steps

## File Naming Patterns



## Best Practices

- Always validate cleaned data structure
- Document schema changes in format-data/Readme.md
- Reuse existing cleaning scripts when appropriate
- Ensure data integrity throughout the transformation process