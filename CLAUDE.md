# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a financial data audit and processing system with MCP integration for advanced financial data querying. The project processes raw financial CSV files into structured relational data tables with comprehensive validation.

## Architecture Overview

### Core Components
- **Data Processing Pipeline**: Raw CSV → Cleaning scripts → Structured output
- **MCP Integration**: Real-time financial data querying through Model Context Protocol
- **Validation System**: Comprehensive financial data validation with accounting checks
- **Accounting Logic Engine**: Built-in accounting rules and business type identification

### Key Technologies
- **Pandas**: Primary data manipulation library
- **MCP Protocol**: For AI-assisted financial data querying
- **Financial Data Models**: Enhanced balance sheets with hierarchical structures
- **Accounting Rules Engine**: Subject classification and balance validation

## Directory Structure

```
├── raw-data/           # Raw CSV files
│   └── Fin/           # Financial source data
├── cleaning/          # Python cleaning and validation scripts
├── format-data/       # Cleaned CSV output files
│   └── financial/     # Enhanced financial data tables
├── mcp/              # MCP server for financial data querying
└── operation/        # Operational scripts
```

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Data Processing
```bash
# Run financial data validation
python cleaning/financial_validation.py

# Adjust opening balances
python cleaning/adjust_opening_balance.py

# Convert CSV files to UTF-8 encoding
python cleaning/convert_to_utf8.py
```

### MCP Server Operations
```bash
# Start financial data MCP server (auto-detects virtual environment)
python mcp/run_financial_mcp.py

# Direct MCP server execution (for debugging)
python mcp/financial_data_mcp.py
```

### Data Analysis
```bash
# Quick data validation
python -c "import pandas as pd; df = pd.read_csv('format-data/financial/final_enhanced_balance.csv'); print(df.info())"

# Check data file sizes
ls -la format-data/financial/
```

## Key Data Files

### Processed Files (format-data/financial/)
- `final_enhanced_balance.csv`: 8,666×17 enhanced balance sheet (2023-2025)
- `final_voucher_detail.csv`: 52,170×27 voucher transaction details (2024-2025)

## MCP Integration Features

The MCP server provides real-time access to financial data through:
- `query_balance_sheet`: Filter balance sheet data with accounting validation
- `query_voucher_details`: Search voucher transactions with business type identification
- `analyze_subject_hierarchy`: Analyze subject relationships and hierarchy
- `search_transactions`: Keyword search in vouchers with fuzzy matching
- `get_financial_summary`: Get aggregated statistics
- `validate_data_consistency`: Verify balance-voucher consistency
- `find_subject_by_name`: Smart subject name lookup
- `query_dimension_details`: Detailed dimension analysis

## Data Processing Workflow

1. **Raw Data**: CSV files in `raw-data/Fin/`
2. **Cleaning**: Scripts in `cleaning/` directory
3. **Enhanced Output**: Structured CSV files with hierarchical coding
4. **MCP Integration**: Real-time query access with accounting logic
5. **Validation**: Comprehensive accounting validation

## Financial Data Schema

### Enhanced Balance Sheet Features
- Hierarchical subject coding with parent-child relationships
- Dimension row identification for multi-dimensional accounting
- Multi-level accounting validation with balance direction checks
- Support for various financial dimensions (supplier, customer, department)

### Validation Rules
- Accounting equation validation (Assets = Liabilities + Equity)
- Year-over-year continuity checks
- Hierarchy correctness validation
- Voucher-to-balance reconciliation
- Subject balance direction validation (asset/debit, liability/credit)

## MCP Server Architecture

### Configuration
- Standard `.mcp.json` configuration in project root
- Automatic virtual environment detection
- Cross-platform support (Windows/Linux/macOS)

### Data Loading
- Optimized CSV loading with memory efficiency
- Automatic path resolution for portability
- Data type optimization for financial data

### Query Capabilities
- Multi-dimensional filtering (company, period, subject, dimension)
- Hierarchical subject queries with path syntax
- Smart fuzzy matching for subject names
- Accounting rule enforcement