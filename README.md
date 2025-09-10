# 🚀 Automated EDA & Visualization by Multi-Agent Chat

A sophisticated system that uses multiple AI agents to automatically perform Exploratory Data Analysis (EDA) and generate visualizations from CSV data. The system employs DeepSeek LLM for intelligent planning, code generation, and reporting while maintaining security through sandboxed execution.

## ✨ Features

- **Multi-Agent Architecture**: Specialized agents for planning, coding, critiquing, and reporting
- **Intelligent EDA Planning**: AI-driven analysis prioritization based on data characteristics
- **Secure Code Execution**: Sandboxed environment with whitelisted imports only
- **Automatic Visualization**: Generates matplotlib-based plots with proper labeling
- **Quality Assurance**: Built-in linter and critic for code quality
- **Comprehensive Reporting**: Markdown reports with actionable insights
- **JSON Contracts**: Structured data flow with validation
- **Deterministic Components**: Profiling and execution without LLM dependency

## 🏗️ Architecture

```
CSV → Profiler → Planner → Code Writer → Executor → Critic → Reporter
                    ↓           ↓           ↓         ↓
                 EDA Plan   Python Code  Plots   Final Report
```

### Agents
- **Orchestrator**: Coordinates the entire pipeline
- **Profiler**: Deterministic CSV analysis and profiling
- **Planner**: AI-driven EDA plan generation
- **Code Writer**: Python code generation for visualizations
- **Executor**: Secure sandboxed code execution
- **Critic**: Code quality review and fixes
- **Reporter**: Final markdown report generation

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- DeepSeek API key

### Installation

1. **Clone and setup**:
```bash
cd automated_eda
pip install -r requirements.txt
```

2. **Set API key**:
```bash
export DEEPSEEK_API_KEY="your_api_key_here"
```

3. **Run analysis**:
```bash
python main.py tests/sample.csv
```

### Example Usage

```bash
# Basic analysis
python main.py data.csv

# With custom goal
python main.py data.csv --goal "Focus on seasonality and anomalies"

# With specific number of items
python main.py data.csv --max-items 10

# With API key
python main.py data.csv --api-key YOUR_API_KEY
```

## 📊 Output Structure

```
automated_eda/
├── artifacts/          # Generated PNG plots
│   ├── fig_q1_1.png
│   ├── fig_q2_1.png
│   └── ...
├── logs/              # Execution logs
│   └── last_run.json
├── report/            # Final report
│   └── report.md
└── ...
```

## 🔧 Configuration

### Environment Variables
- `DEEPSEEK_API_KEY`: Your DeepSeek API key

### Command Line Options
- `--goal`: Analysis focus (default: "General EDA")
- `--max-items`: Maximum EDA items (default: 8)
- `--api-key`: DeepSeek API key override

## 🛡️ Security Features

### Sandbox Execution
- Whitelisted imports only (`pandas`, `numpy`, `matplotlib`, `scipy`)
- Forbidden modules: `os`, `sys`, `subprocess`, `socket`, etc.
- Resource limits: 10s timeout, memory caps
- File access restricted to `./artifacts` directory

### Code Validation
- Automatic linter rules
- Security pattern detection
- Manifest validation
- Error handling and recovery

## 📋 Linter Rules

The system automatically checks for:
- Missing axis labels or titles
- High cardinality categorical variables
- Skewed distributions without log scale
- Too many axis ticks
- High missing value rates
- Empty or sparse plots
- Oversized heatmaps

## 🎯 Example Analysis

Given a transaction dataset, the system will:

1. **Profile**: Analyze 100 rows, 8 columns, detect data types
2. **Plan**: Create 6-8 prioritized analysis items
3. **Execute**: Generate visualizations for each item
4. **Report**: Produce insights and next questions

### Sample Output
```markdown
# EDA Analysis Report

## Data Overview
- **Total Rows**: 100
- **Total Columns**: 8

## Analysis Results
### Distribution of Amount
- Generated histogram and boxplot
- Identified right-skewed distribution
- Suggested log transformation

### Category Analysis
- Electronics: 40% of transactions
- Clothing: 30% of transactions
- Books: 30% of transactions

## Next Questions
- What are the strongest correlations between variables?
- Are there any temporal patterns in the data?
- What are the main outliers and their potential causes?
```

## 🧪 Testing

### Smoke Test
```bash
python main.py tests/sample.csv
```

### Expected Outputs
- ✅ 6-8 PNG files in `./artifacts/`
- ✅ JSON log in `./logs/last_run.json`
- ✅ Markdown report in `./report/report.md`

## 📚 API Reference

### Main Classes

#### `EDAOrchestrator`
Main coordinator class that runs the entire pipeline.

```python
orchestrator = EDAOrchestrator(api_key="your_key")
result = orchestrator.run_eda("data.csv", "General EDA", max_items=8)
```

#### `CSVProfiler`
Deterministic CSV analysis and profiling.

```python
profiler = CSVProfiler()
profile = profiler.profile("data.csv")
```

#### `SandboxExecutor`
Secure code execution environment.

```python
executor = SandboxExecutor()
result = executor.execute(code, dataframe, manifest_schema)
```

### Agent Classes

- `PlannerAgent`: Creates EDA plans
- `CodeWriterAgent`: Generates Python code
- `CriticAgent`: Reviews and fixes code
- `ReporterAgent`: Creates final reports

## 🔍 Troubleshooting

### Common Issues

**API Key Error**:
```bash
export DEEPSEEK_API_KEY="your_key_here"
```

**Import Errors**:
```bash
pip install -r requirements.txt
```

**Permission Errors**:
```bash
chmod 755 automated_eda/
```

**Large File Issues**:
The system automatically samples large files (>50MB) for performance.

### Debug Mode
Add debug prints in `main.py` to see intermediate results.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- DeepSeek for providing the LLM API
- The pandas, matplotlib, and numpy communities
- Contributors and testers

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the smoke test documentation
3. Open an issue with detailed error information

---

**Built with ❤️ for automated data analysis**
