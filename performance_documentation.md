**NOTE**
this code has been developed for exercise purpose. Right now performance command is not included in Ersilia's CLI.
The other comands are callbacked but the arguments for them where not included, therefore the file will not pass the test for **eos4e40**.

# Ersilia Performance Command

## Overview

The `ersilia performance` command provides comprehensive performance analysis for Ersilia models. It measures computational performance metrics including CPU usage, memory consumption, and execution timing while running a specified model from the model hub. (dockerhub, repo, s3 etc…).
   
## Installation and Setup

### Windows Setup with WSL

1. **Install WSL and Ubuntu:**[1](https://learn.microsoft.com/en-us/windows/wsl/install)
```powershell
wsl --install -d Ubuntu
```

2. **Install Miniconda in WSL:**[2](https://ersilia.gitbook.io/ersilia-book/ersilia-model-hub/local-inference)
```bash
wsl -d Ubuntu
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh
~/miniconda3/bin/conda init bash
~/miniconda3/bin/conda init zsh
```

3. **Create Conda environment:**
```bash
conda create -n ersilia python=3.12
conda activate ersilia
```

4. **Clone and install Ersilia:**[3](https://ersilia.gitbook.io/ersilia-book/ersilia-model-hub/developer-docs#the-ersilia-cli)
```bash
# Fork the repo first on GitHub
git clone https://github.com/<your-username>/ersilia.git
cd ersilia
pip install -e .
```

5. **Install Docker:**
All models incorporated in Ersilia are dockerized[4](https://hub.docker.com/u/ersiliaos) for easy deployment. While the dockerization step happens as part of our CI/CD workflows, it is recommended to install Docker for model testing purposes.
```bash
sudo apt update
sudo apt install docker.io
sudo usermod -aG docker $USER
newgrp docker
```

or directly from [Docker Website](https://www.docker.com/)

## Command Usage

```bash
ersilia performance <MODEL_ID> [OPTIONS]
```

## Arguments

- `MODEL_ID` - The identifier of the model to analyze (e.g., `eos4e40`)

## Options

- `--samples, -n INTEGER` - Number of input samples for testing (default: 100)
- `--help` - Show help message and exit

## Examples

### Basic Usage

```bash
# Basic usage (default settings = 100 samples)
ersilia performance eos4e40
```

### Custom Sample Size

```bash
# Custom input sample size
ersilia performance eos4e40 --samples 200
```

### Output
```
————— Performance Report —————
Model:    eos4e40
CPU Avg:  72.30%
Mem Peak: 512 MiB
Duration: 8.30s
—————————————————————————————
```

## Architecture

The command follows Ersilia's modular CLI design, reusing existing commands:

1. **Fetch** - Downloads the specified model from DockerHub
2. **Serve** - Starts the model container
3. **Example** - Creates sample input data for testing
4. **Run** - Executes the model while monitoring resource usage
5. **Close** - Shuts down the model
6. **Generate Report** - Provides detailed performance metrics


### Performance Monitoring

**Why Docker Stats API?**[5](https://docs.docker.com/reference/cli/docker/container/stats/)
After gathering some examples Docker's native stats API has been choosen over alternatives like `psutil` that would measure all system processes, not just the model. Docker Stats API offers:

- **Isolation**: Measures only the model container, not the entire Python process
- **Accuracy**: Excludes CLI overhead and system processes
- **Native integration**: Docker already provides these metrics
- **Container-specific**: Models run in Docker, so container stats are most relevant

### Metric Calculations
Next, some information on the metrics has been researched and added to the documentation to deep the knowladge on computational performance of a model.

**CPU Percentage:**

```python
cpu_delta = current_cpu_usage - previous_cpu_usage
system_delta = current_system_usage - previous_system_usage
cpu_percent = (cpu_delta / system_delta) * 100
```

- `cpu_delta`: CPU nanoseconds used by container in the measurement period
- `system_delta`: Total system CPU nanoseconds in the same period
- Result: Percentage of system CPU used by the container

**Memory Peak:**
- Raw value from Docker stats in bytes
- Converted to MiB (1 MiB = 1,048,576 bytes)
- Tracks maximum memory usage during execution

**Duration:**
- Measured using Python's `time.time()`
- Captures total execution time of `model.run()`
- Includes model processing and I/O operations

### Code Structure

```
ersilia/cli/commands/performance.py    # Main implementation
ersilia/cli/cmd.py                     # Command registration
test/cli/test_performance.py           # Test suite
```

Key design decisions:
- **Temporary files**: Using `tempfile.TemporaryDirectory()` for automatic cleanup
- **Error handling**: degradation when Docker is unavailable
- **Modular design**: Reuses existing CLI commands rather than duplicating logic

## Testing

Run the test suite:
```bash
python -m pytest test/cli/test_performance.py -v
```

This test should cover aside of the basic command execution, the docker integration, the error scenarios and the performance metric calculations.

## Resources

### Technical Documentation
1. https://learn.microsoft.com/en-us/windows/wsl/install
2. https://ersilia.gitbook.io/ersilia-book/ersilia-model-hub/local-inference
3. https://ersilia.gitbook.io/ersilia-book/ersilia-model-hub/developer-docs#the-ersilia-cli
4. https://hub.docker.com/u/ersiliaos
5. https://docs.docker.com/reference/cli/docker/container/stats/


- [Ersilia Documentation](https://ersilia.gitbook.io/)
- [Ersilia CLI Book](https://ersilia.gitbook.io/ersilia-book/)
- [Docker Container Stats API](https://docs.docker.com/reference/cli/docker/container/stats/)
- [Docker Python Client](https://docker-py.readthedocs.io/en/stable/containers.html)

### Implementation References
- [Docker Container CPU Usage Calculation](https://stackoverflow.com/questions/30271942/get-docker-container-cpu-usage-as-percentage): code in JAVA
- [Docker Stats Programming Examples](https://stackoverflow.com/questions/42968626/getting-docker-stats-programmatically): reference to get the desired container and stats. In the code has been used in the following:

```python
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

...

stats = container.stats(stream=False)
```

- [Python Docker Container Monitoring](https://medium.com/@martinkarlsson.io/control-and-monitor-your-docker-containers-with-python-7a3bdc4b88fa): *Logic written in words*
- [CPU and Memory Monitoring Alternatives](https://stackoverflow.com/questions/62404393/how-to-calculate-the-amount-of-cpu-and-memory-used-by-a-python-script)