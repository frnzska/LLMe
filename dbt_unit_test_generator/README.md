# DBT Unit Test Generator

A tool that automatically generates unit tests for your dbt models using OpenAI.

## Overview

This tool helps scaffold unit tests for your dbt models. It analyzes your dbt model and generates appropriate test cases.

## Features

- Automatic test case generation for dbt models
- Configurable OpenAI model selection (default: gpt-4-0)

## Usage

```bash
python dbt_unit_test_generator.py \
    --model_path testing/data/models/customer_order_summary.sql \
    --output_path testing/data/generated_results
```

## Output

The output is a YAML file with the unit tests. See model and result in `testing/data/generated_results/`
