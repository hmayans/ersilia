import click

from ersilia.core import model

from .fetch import fetch_cmd
from .serve import serve_cmd
from .example import example_cmd
from .run import run_cmd
from .close import close_cmd


from ... import ErsiliaModel
from .. import echo
from . import ersilia_cli

import time
import statistics
import docker
from datetime import datetime

def performance_cmd():
    """ 
    Measures computational performance from a specified model.

    This command allows users to measure the computational performance 
    (CPU, memory, duration) of running a specified model from the model hub (dockerhub, repo, s3 etc…).
    
    Returns
    -------
    function
        The serve command function to be used by the CLI and for testing in the pytest.

    Examples
    --------
    .. code-block:: console

    Serve a model by its ID:
        $ ersilia performance <model_id> --port 8080

    Serve a model and track the session:
        $ ersilia performance <model_id> --track
"""

    # Example usage: ersilia performance <model_id>
    @ersilia_cli.command(short_help="Measure performance of model", 
                         help="""Run performance analysis on a specified model
                         
                         This command will:
                         - Fetch model as in ersilia fetch $MODEL_ID --from_dockerhub
                         - Serve model as in ersilia serve $MODEL_ID
                         - Get 100 example inputs as in ersilia example -n 100 -f my_input.csv
                         - Run the model as in ersilia run -i my_input.csv -o my_output.csv
                         - Evaluate computational performance of the run
                         - Close the model as in ersilia close
                         - Print a neatly formatted report

                         Example usage:
                            ersilia performance eos4e40
                            ersilia performance eos4e40 --samples 200 --detailed
                            ersilia performance eos4e40 --output-dir ./reports
                         """)
    @click.argument("model", type=click.STRING)
    @click.option(
        "--samples", 
        "-n", 
        default=100, 
        type=click.INT, 
        help="Number of input samples for testing (default: 100)"
        )
    # Add the new flag for tracking the serve session
    # @click.option(
    #     "--output-dir",
    #     "-o",
    #     default=None,
    #     type=str,
    #     help="Directory to save performance results and CSV files"
    #     )

    def performance(model, samples):
        """Run performance analysis on a specified model."""

        fetch = fetch_cmd()
        serve = serve_cmd()
        example = example_cmd()
        run = run_cmd()
        close = close_cmd()

        echo(f"Running performance analysis on model: {model}")

        model = ErsiliaModel(model)

        #temporal files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_file = f"performance_input_{model}_{timestamp}.csv"
        output_file = f"performance_output_{model}_{timestamp}.csv"

        # 1. Fetch the model
        echo("Fetching the model...")
        fetch.callback(model, from_dockerhub=True)

        # 2. Serve the model
        echo("Serving the model...")
        serve.callback(model)

        # 3. Get example inputs
        echo(f"Generating {samples} example inputs...")
        example.callback(model, num_samples=samples, file_name=input_file)

        # 4. Run the model
        echo("Running model and measuring performance...")
        client = docker.from_env()
        container = client.containers.list(filters={"ancestor": model})[0]

        cpu_samples, mem_samples = [], []
        start_time = time.time()

        # Start model run
        run.callback(input=input_file, output=output_file, batch_size=100)

        # Collect one snapshot after run finishes
        stats = container.stats(stream=False)
        cpu_percent = stats["cpu_stats"]["cpu_usage"]["total_usage"] / stats["cpu_stats"]["system_cpu_usage"] * 100
        mem_usage = stats["memory_stats"]["usage"]

        cpu_samples.append(cpu_percent)
        mem_samples.append(mem_usage)

        end_time = time.time()
        runtime_duration = end_time - start_time

        # 5. Close the model
        echo("Closing the model...")
        close.callback()
        echo("Model closed successfully.")

        # 6. Report
        cpu_avg = statistics.mean(cpu_samples) if cpu_samples else 0.0
        mem_peak = max(mem_samples) if mem_samples else 0

        print("\n————— Performance Report —————")
        print(f"Model:    {model}")
        print(f"CPU Avg:  {cpu_avg:.2f}%")
        print(f"Mem Peak: {mem_peak/1024/1024:.0f} MiB")
        print(f"Duration: {runtime_duration:.2f}s")
        print("—————————————————————————————")

    return performance