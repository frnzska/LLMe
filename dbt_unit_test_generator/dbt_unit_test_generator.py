import argparse
import os
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

EXAMPLE_MODEL = """
{{
    config(
        materialized='incremental'
    )
}}

select * from {{ ref('events') }}
{% if is_incremental() %}
where event_time > (select max(event_time) from {{ this }})
{% endif %}
"""

EXAMPLE_UNIT_TEST = """
unit_tests:
  - name: my_incremental_model_full_refresh_mode
    model: my_incremental_model
    overrides:
      macros:
        # unit test this model in "full refresh" mode
        is_incremental: false 
    given:
      - input: ref('events')
        rows:
          - {event_id: 1, event_time: 2020-01-01}
    expect:
      rows:
        - {event_id: 1, event_time: 2020-01-01}

  - name: my_incremental_model_incremental_mode
    model: my_incremental_model
    overrides:
      macros:
        # unit test this model in "incremental" mode
        is_incremental: true 
    given:
      - input: ref('events')
        rows:
          - {event_id: 1, event_time: 2020-01-01}
          - {event_id: 2, event_time: 2020-01-02}
          - {event_id: 3, event_time: 2020-01-03}
      - input: this 
        # contents of current my_incremental_model
        rows:
          - {event_id: 1, event_time: 2020-01-01}
    expect:
      # what will be inserted/merged into my_incremental_model
      rows:
        - {event_id: 2, event_time: 2020-01-02}
        - {event_id: 3, event_time: 2020-01-03}
"""


def read_model_file(model_path: str) -> str:
    """Read the contents of a dbt model file."""
    with open(model_path, 'r') as f:
        return f.read()


def generate_unit_test(model_content: str, model_name: str, model: str = "gpt-4-0") -> str:
    """Generate a unit test using OpenAI."""
    client = OpenAI()
    
    prompt = f"""
    Here's an example of a dbt model and its corresponding unit test:

    Model:
    {EXAMPLE_MODEL}

    Unit Test as content of a YAML file:
    {EXAMPLE_UNIT_TEST}

    Create a dbt unit test, that contains only valid YAML for the following model:
    
    {model_content}
    
    The test should:
    1. Include appropriate test cases
    2. Follow dbt unit test structure
    3. Test edge cases
    4. Include input and expected output data
    5. Output data is only in YAML format
    """
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates dbt unit tests."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    yaml_content = response.choices[0].message.content.strip()
    yaml_content = yaml_content.replace('```yaml', '').replace('```', '').strip()
    return yaml_content



def save_unit_test(test_content: str, output_path: str, model_name: str) -> None:
    """Save the generated unit test to a file."""
    # if the output path doesn't exist, create it
    os.makedirs(output_path, exist_ok=True)

    test_file_name = f"unit_test_{model_name}.yml"
    test_file_path = os.path.join(output_path, test_file_name)
    
    with open(test_file_path, 'w') as f:
        f.write(test_content)
    print(f"Unit test saved to: {test_file_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate dbt unit tests using OpenAI')
    parser.add_argument('--model_path', required=True, help='Path to the dbt model file')
    parser.add_argument('--output_path', required=True, help='Path to save the generated test')
    parser.add_argument('--model', default='gpt-4o', help='OpenAI model to use')
    
    args = parser.parse_args()
    model_name = Path(args.model_path).stem
    
    try:
        model_content = read_model_file(args.model_path)
        test_content = generate_unit_test(model_content, model_name, args.model)
        save_unit_test(test_content, args.output_path, model_name)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()