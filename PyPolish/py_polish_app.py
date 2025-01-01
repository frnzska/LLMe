"""Python Code Optimizer using LLMs.

This module provides a Gradio interface for optimizing Python code using various LLM models.
It supports OpenAI's GPT models and Anthropic's Claude model.
"""

import os
import time
from dotenv import load_dotenv
import gradio as gr
from openai import OpenAI
import anthropic


def load_env() -> dict:
    """Load environment variables from .env file.

    Returns:
        dict: Dictionary containing API keys
    """
    load_dotenv()
    return {
        'openai_key': os.getenv('OPENAI_API_KEY'),
        'anthropic_key': os.getenv('ANTHROPIC_API_KEY')
    }


def improve_code(code: str, model: str) -> str:
    """Improve the given Python code using specified LLM model.

    Args:
        code: The Python code to improve
        model: The LLM model to use for improvement

    Returns:
        str: Improved version of the code
    """
    system_prompt = (
        "You are a Python code optimization expert. "
        "Improve the given code for efficiency. "
        "Do only deliver the code, no other explanation."
    )
    user_prompt = f"Please improve this Python code:\n\n{code}"
    
    if model in ["gpt-4", "gpt-3.5-turbo"]:
        client = OpenAI()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content
    
    if model == "claude-3-sonnet-20240229":
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"{system_prompt}\n\n{user_prompt}"
            }],
            temperature=0.7
        )
        return response.content[0].text
    
    return "Invalid model choice"


def model_mapping(code: str, llm_choice: str) -> str:
    """Map friendly model names to actual model identifiers and improve code.

    Args:
        code: The Python code to improve
        llm_choice: The selected model name

    Returns:
        str: Improved code or error message
    """
    model_mapping = {
        "GPT-4": "gpt-4",
        "GPT-3.5": "gpt-3.5-turbo",
        "Claude": "claude-3-sonnet-20240229"
    }
    model = model_mapping.get(llm_choice)
    return improve_code(code, model) if model else "Invalid LLM choice"


def run_code(code: str) -> float:
    """Execute the given code and measure its runtime.

    Args:
        code: Python code to execute

    Returns:
        float: Execution time in seconds
    """
    start_time = time.time()
    exec(code)
    return time.time() - start_time


def create_gradio_interface() -> gr.Blocks:
    """Create the Gradio interface for the code optimizer.

    Returns:
        gr.Blocks: Configured Gradio interface
    """
    with gr.Blocks(title="Python Code Optimizer") as app:
        gr.Markdown("# Python Code Optimizer")
        gr.Markdown("Enter your Python code and select an LLM to get optimization suggestions.")
        
        with gr.Row():
            with gr.Column():
                input_code = gr.Code(
                    label="Input Python Code",
                    language="python",
                    lines=10
                )
                llm_choice = gr.Radio(
                    choices=["GPT-4", "GPT-3.5", "Claude"],
                    label="Select LLM",
                    value="GPT-4"
                )
                improve_btn = gr.Button("Improve Code")
            
            with gr.Column():
                output_code = gr.Code(
                    label="Improved Code",
                    language="python",
                    lines=10
                )
   
        with gr.Row():
            with gr.Column():
                run_btn = gr.Button("Run Code Locally")
                run_time = gr.Number(label="Execution Time (seconds)")

            with gr.Column():
                run_improved_btn = gr.Button("Run Improved Code Locally")
                run_improved_time = gr.Number(label="Execution Time (seconds)")
        
        improve_btn.click(
            fn=model_mapping,
            inputs=[input_code, llm_choice],
            outputs=[output_code]
        )
        run_btn.click(
            fn=run_code,
            inputs=[input_code],
            outputs=[run_time]
        )
        run_improved_btn.click(
            fn=run_code,
            inputs=[output_code],
            outputs=[run_improved_time]
        )
    
    return app


def main() -> None:
    """Initialize and run the application."""
    try:
        api_keys = load_env()
        if not api_keys['openai_key'] and not api_keys['anthropic_key']:
            raise ValueError("No API keys found in environment variables")
        
        app = create_gradio_interface()
        print("\nStarting Python Code Optimizer...")
        print("Once running, open your browser to: http://localhost:7860\n")
        app.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True
        )
    except Exception as e:
        print(f"\nError starting the application: {str(e)}")
        raise


if __name__ == "__main__":
    main()

