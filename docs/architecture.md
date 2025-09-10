# Automated EDA & Visualization Architecture

## Overview
This system implements a multi-agent approach to automated Exploratory Data Analysis (EDA) using Large Language Models (LLMs) for intelligent planning, code generation, and reporting.

## System Architecture

### Core Components

#### 1. Orchestrator (`main.py`)
- **Role**: Coordinates the entire EDA pipeline
- **Responsibilities**:
  - Sequence agent interactions
  - Validate JSON contracts
  - Handle retries and error recovery
  - Generate final outputs

#### 2. Agents (`agents/`)

##### Planner Agent (`planner.py`)
- **Role**: Converts data profile + user goal into prioritized EDA plan
- **Input**: Profile JSON, user goal, constraints
- **Output**: EDA plan with prioritized items
- **LLM**: DeepSeek for intelligent planning

##### Code Writer Agent (`coder.py`)
- **Role**: Generates Python code for visualizations
- **Input**: Plan item, profile, constraints
- **Output**: Python code + manifest schema
- **LLM**: DeepSeek for code generation

##### Critic Agent (`critic.py`)
- **Role**: Reviews execution results and proposes fixes
- **Input**: Code output, execution result
- **Output**: Critique with potential fixes
- **LLM**: DeepSeek for intelligent critique

##### Reporter Agent (`reporter.py`)
- **Role**: Generates final markdown report
- **Input**: Analysis highlights, profile
- **Output**: Markdown report + next questions
- **LLM**: DeepSeek for report generation

#### 3. Runtime Components (`runtime/`)

##### Profiler (`profiler.py`)
- **Role**: Deterministic CSV analysis
- **Features**:
  - Data type inference
  - Missing value analysis
  - Basic statistics
  - Target column detection
- **Output**: Structured profile JSON

##### Executor (`executor.py`)
- **Role**: Secure code execution
- **Features**:
  - Sandboxed execution environment
  - Security constraints (whitelisted imports)
  - Resource limits (timeout, memory)
  - Manifest validation
  - Evidence extraction
  - Linter rules

#### 4. LLM Integration (`llm/`)

##### DeepSeek Client (`deepseek_client.py`)
- **Role**: LLM API wrapper
- **Features**:
  - JSON-only response format
  - Error handling
  - Timeout management
  - System prompt management

## Data Flow

```
CSV Input
    ↓
Profiler (Deterministic)
    ↓
Profile JSON
    ↓
Planner Agent (LLM)
    ↓
EDA Plan
    ↓
For each plan item:
    Code Writer (LLM) → Executor → Critic (LLM) → [Fix if needed]
    ↓
Analysis Highlights
    ↓
Reporter Agent (LLM)
    ↓
Final Report + Artifacts
```

## JSON Contracts

### Profile Schema
```json
{
  "rows_total": 0,
  "rows_sampled": 0,
  "memory_estimate_mb": 0.0,
  "columns": [...],
  "suspected_target": null
}
```

### EDA Plan Schema
```json
{
  "eda_plan": [
    {
      "id": "string",
      "goal": "string",
      "plots": ["histogram", "boxplot", ...],
      "priority": 1,
      "columns": ["col1", "col2"],
      "notes": "string"
    }
  ]
}
```

### Code Output Schema
```json
{
  "title": "string",
  "python": "string",
  "expected_outputs": ["path1.png", "path2.png"],
  "manifest_schema": {...}
}
```

### Execution Result Schema
```json
{
  "exec_ok": true,
  "stdout": "string",
  "error": "string",
  "manifest": {...},
  "evidence": {...},
  "linter_flags": [...]
}
```

## Security Model

### Sandbox Constraints
- **Forbidden Modules**: `os`, `sys`, `subprocess`, `socket`, `http`, etc.
- **Forbidden Functions**: `open`, `file`, `input`, `exec`, `eval`, etc.
- **Resource Limits**: 10s timeout per cell, memory caps
- **File Access**: Only `./artifacts` directory for outputs

### Whitelisted Imports
- `pandas`, `numpy`, `matplotlib`, `scipy`
- Safe builtins only
- No network or filesystem access

## Linter Rules

### Automatic Checks
- `MISSING_LABELS`: Missing axis labels or titles
- `HIGH_CARDINALITY`: Categorical columns with >15 unique values
- `HIGH_SKEW_NO_LOG`: Numeric columns with |skew| > 2 without log scale
- `MANY_TICKS`: Axis with >20 ticks
- `HIGH_NA_DROP`: >20% missing values dropped
- `EMPTY_PLOT`: <50 rows plotted
- `HEATMAP_TOO_WIDE`: >30 numeric features

## Error Handling

### LLM Failures
- Fallback to deterministic alternatives
- Graceful degradation
- Error logging

### Execution Failures
- Sandbox protection
- Detailed error messages
- Retry mechanisms

### Validation Failures
- JSON schema validation
- Contract enforcement
- Type checking

## Performance Considerations

### Optimization Strategies
- Data sampling for large files
- Parallel processing where possible
- Caching of intermediate results
- Resource monitoring

### Scalability
- Configurable limits
- Memory-efficient processing
- Timeout management
- Batch processing support

## Extensibility

### Adding New Agents
1. Implement agent class with required interface
2. Add to orchestrator workflow
3. Define JSON contracts
4. Update documentation

### Adding New Linter Rules
1. Implement rule in executor
2. Add to linter flags
3. Update critic prompts
4. Test with sample data

### Adding New Plot Types
1. Update plot type enums
2. Extend code writer prompts
3. Add validation rules
4. Update documentation

## Testing Strategy

### Unit Tests
- Individual agent testing
- Component isolation
- Mock LLM responses

### Integration Tests
- End-to-end pipeline
- Real data scenarios
- Error condition testing

### Smoke Tests
- Basic functionality verification
- Sample data validation
- Output format checking

## Deployment Considerations

### Environment Setup
- Python 3.10+ requirement
- Package dependencies
- API key configuration
- Directory permissions

### Monitoring
- Execution logs
- Performance metrics
- Error tracking
- Resource usage

### Maintenance
- Regular dependency updates
- API key rotation
- Log cleanup
- Performance optimization
