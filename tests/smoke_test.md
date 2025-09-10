# Smoke Test for Automated EDA System

## Test Overview
This document describes the smoke test for the Automated EDA & Visualization system.

## Test Data
- **File**: `tests/sample.csv`
- **Rows**: 100 transactions
- **Columns**: 8 (transaction_id, date, amount, category, customer_id, items, region, payment_method)
- **Data Types**: Mixed (numeric, categorical, datetime)

## Expected Outputs

### 1. Artifacts Directory
- `./artifacts/*.png` - Generated visualization files
- At least 6-8 plot files based on EDA plan

### 2. Logs Directory
- `./logs/last_run.json` - Complete execution log with:
  - Profile data
  - EDA plan
  - Execution results for each item
  - Final report

### 3. Report Directory
- `./report/report.md` - Markdown report containing:
  - Data overview
  - Analysis results
  - Figure references
  - Next questions

## Test Commands

### Basic Test
```bash
cd automated_eda
python main.py tests/sample.csv
```

### With Custom Goal
```bash
python main.py tests/sample.csv --goal "Focus on transaction patterns and seasonality"
```

### With API Key
```bash
python main.py tests/sample.csv --api-key YOUR_DEEPSEEK_API_KEY
```

## Success Criteria

1. ✅ System runs without errors
2. ✅ Generates at least 6 EDA plan items
3. ✅ Creates PNG files in artifacts directory
4. ✅ Produces valid JSON logs
5. ✅ Generates readable markdown report
6. ✅ LLMs never consume images (text-only reasoning)
7. ✅ Linter flags high skew without log scale
8. ✅ Critic proposes fixes when needed
9. ✅ Reporter includes actionable next questions

## Troubleshooting

### Common Issues
- **API Key Error**: Set `DEEPSEEK_API_KEY` environment variable
- **Import Errors**: Install requirements with `pip install -r requirements.txt`
- **Permission Errors**: Ensure write access to artifacts, logs, and report directories

### Debug Mode
Add debug prints to see intermediate results:
```python
# In main.py, add after each step:
print(f"Debug: {variable_name}")
```
