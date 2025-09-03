import os
import click

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
import tempfile

try:
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

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
                            ersilia performance eos4e40 --samples 200 
                         """)
    @click.argument("model_id", type=click.STRING)
    @click.option(
        "--samples", 
        "-n", 
        default=100, 
        type=click.INT, 
        help="Number of input samples for testing (default: 100)"
        )

    def performance(model_id, samples):
        """Run performance analysis on a specified model."""

        fetch = fetch_cmd()
        serve = serve_cmd()
        example = example_cmd()
        run = run_cmd()
        close = close_cmd()

        echo(f"Running performance analysis on model: {model_id}")
        with tempfile.TemporaryDirectory() as temp_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            input_file = os.path.join(temp_dir, f"performance_input_{model_id}_{timestamp}.csv")
            output_file = os.path.join(temp_dir, f"performance_output_{model_id}_{timestamp}.csv")

            cpu_samples, mem_samples = [], []
            
            try:
                # 1. Fetch the model
                echo("Fetching the model...")
                fetch.callback(model_id, from_dockerhub=True)

                # 2. Serve the model
                echo("Serving the model...")
                serve.callback(model_id)

                # 3. Get example inputs
                echo(f"Generating {samples} example inputs...")
                example.callback(model_id, num_samples=samples, file_name=input_file)

                # 4. Setup Docker monitoring
                container = None
                if DOCKER_AVAILABLE:
                    try:
                        client = docker.from_env()
                        containers = client.containers.list()
                        # Find container with model_id in name or image
                        for c in containers:
                            if (model_id.lower() in c.name.lower() or 
                                model_id.lower() in str(c.image).lower()):
                                container = c
                                break
                    except Exception as e:
                        echo(f"Warning: Could not connect to Docker: {e}")

                # 5. Run the model and measure performance
                echo("Running model and measuring performance...")
                start_time = time.time()

                # Run the model
                run.callback(input=input_file, output=output_file)

                # Collect performance metrics after run
                if container:
                    try:
                        stats = container.stats(stream=False)
                        
                        # Calculate CPU percentage
                        cpu_delta = (stats["cpu_stats"]["cpu_usage"]["total_usage"] - 
                                   stats["precpu_stats"]["cpu_usage"]["total_usage"])
                        system_delta = (stats["cpu_stats"]["system_cpu_usage"] - 
                                      stats["precpu_stats"]["system_cpu_usage"])
                        
                        if system_delta > 0:
                            cpu_percent = (cpu_delta / system_delta) * 100.0
                            cpu_samples.append(cpu_percent)
                        
                        # Memory usage
                        mem_usage = stats["memory_stats"]["usage"]
                        mem_samples.append(mem_usage)
                        
                    except Exception as e:
                        echo(f"Warning: Could not collect performance stats: {e}")

                end_time = time.time()
                runtime_duration = end_time - start_time

                # 6. Close the model
                echo("Closing the model...")
                close.callback()
                echo("Model closed successfully.")

                # 7. Calculate and display results
                cpu_avg = statistics.mean(cpu_samples) if cpu_samples else 0.0
                mem_peak = max(mem_samples) if mem_samples else 0

                print("\n————— Performance Report —————")
                print(f"Model:    {model_id}")
                print(f"CPU Avg:  {cpu_avg:.2f}%")
                print(f"Mem Peak: {mem_peak/1024/1024:.0f} MiB")
                print(f"Duration: {runtime_duration:.2f}s")
                print("—————————————————————————————")

            except Exception as e:
                echo(f"Performance analysis failed: {str(e)}")
                # Try to cleanup
                try:
                    close.callback()
                except:
                    pass
                raise

    return performance