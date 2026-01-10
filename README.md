# GitHub Classroom Autograder

An automated grading system for GitHub Classroom assignments that clones student repositories, runs test scripts, collects performance metrics, and generates a leaderboard with results.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Step 1: Copy the Example Configuration](#step-1-copy-the-example-configuration)
  - [Step 2: Configure the Grader Section](#step-2-configure-the-grader-section)
  - [Step 3: Configure Assignments](#step-3-configure-assignments)
  - [Step 4: Configure SLURM Backend](#step-4-configure-slurm-backend)
- [GitHub Personal Access Token](#github-personal-access-token)
- [Running the Grader](#running-the-grader)
- [Setting Up as a Recurrent Task](#setting-up-as-a-recurrent-task)
- [Test Script Format](#test-script-format)
- [Output Format](#output-format)

## Overview

This grading system automates the process of:
1. Fetching student submissions from GitHub Classroom
2. Cloning student repositories
3. Running test scripts with configurable SLURM resources
4. Collecting results including pass/fail status and performance metrics
5. Generating a JSON leaderboard with all results

## Features

- **Automated GitHub Classroom Integration**: Fetches assignments and submissions via GitHub API
- **SLURM Support**: Execute test scripts with configurable SLURM resources (CPU, memory, GPUs, etc.)
- **Performance Metrics**: Collects runtime statistics from test scripts
- **Flexible Assignment Identification**: Use invite links, slugs, or assignment IDs
- **Blocking/Non-blocking Execution**: Control whether to wait for assignment completion
- **Repository Cleanup**: Option to preserve or delete cloned repositories
- **Leaderboard Generation**: JSON output with all results and metrics

## Installation

1. Clone this repository
2. Install dependencies using `uv` or `pip`:
   ```bash
   uv sync
   # or
   pip install -r requirements.txt
   ```

## Configuration

### Step 1: Copy the Example Configuration

Create your configuration file by copying the example:

```bash
cp grader-config-example.yaml grader-config.yaml
```

### Step 2: Configure the Grader Section

Edit the `grader` section in `grader-config.yaml`:

```yaml
grader:
  working_dir: "/tmp/grader"
  grades_file: "leaderboard.json"
  github_pat: "github_pat_xxxxx"  # Optional, can use ENV variable instead
```

**Field Explanations:**

- **`working_dir`**: Directory where student repositories will be cloned. This directory must exist before running the grader.
- **`grades_file`**: Path to the output JSON file containing all grading results and the leaderboard.
- **`github_pat`**: (Optional) Your GitHub Personal Access Token. Can be omitted if provided via environment variable (see [GitHub Personal Access Token](#github-personal-access-token) section).

### Step 3: Configure Assignments

Add assignments to the `assignments` list. Each assignment can have multiple tasks that run different test scripts with different configurations:

```yaml
assignments:
  - name: "vector-sum"
    invite_link: "https://classroom.github.com/a/example1"
    preserve_repo_files: false

    tasks:
      - name: "test-cpu"
        skip: false
        blocking: true
        test_script_path: "./test_scripts/test_vectorsum_cpu.sh"

        slurm_backend:
          config:
            slurm_partition: "short"
            timeout_min: 60
            mem_gb: 4
            nodes: 1
            tasks_per_node: 1
            cpus_per_task: 2
            gpus_per_node: 0
            
      - name: "test-gpu"
        skip: false
        blocking: true
        test_script_path: "./test_scripts/test_vectorsum_gpu.sh"
        
        slurm_backend:
          config:
            slurm_partition: "gpu"
            timeout_min: 60
            mem_gb: 8
            nodes: 1
            tasks_per_node: 1
            cpus_per_task: 4
            gpus_per_node: 1
```

**Assignment-Level Field Explanations:**

- **`name`** (required): A unique identifier for the assignment. Used as the key in the output JSON.

- **Assignment Identification** (at least one required):
  - **`invite_link`**: The GitHub Classroom assignment invite URL (e.g., `https://classroom.github.com/a/xxxxx`)
  - **`slug`**: The assignment slug from GitHub Classroom (alternative to invite_link)
  - **`id`**: The numeric assignment ID (alternative to invite_link or slug)
  
  Note: You only need to provide **one** of these three identifiers.

- **`preserve_repo_files`** (default: `false`): If `true`, cloned repositories will not be deleted after grading. Useful for debugging.

- **`tasks`** (required): A list of tasks to run for this assignment. Each task represents a different test or evaluation.

**Task-Level Field Explanations:**

- **`name`** (required): A unique identifier for the task within the assignment. Used to identify the task in logs and output.

- **`skip`** (default: `false`): If `true`, this task will be skipped during grading.

- **`blocking`** (default: `false`): If `true`, the grader will wait for this task's execution to complete before proceeding to the next task. Useful for sequential processing or when tasks have dependencies.

- **`test_script_path`** (required): Absolute or relative path to the test script that will be executed in each student's repository for this task.

### Step 4: Configure SLURM Backend for Tasks

The `slurm_backend.config` section within each task accepts parameters that are passed directly to **submitit**, which manages SLURM job submissions. Each task can have different SLURM resource requirements.

```yaml
slurm_backend:
  config:
    slurm_partition: "short"      # SLURM partition name
    timeout_min: 120              # Maximum runtime in minutes
    mem_gb: 8                     # Memory allocation in GB
    nodes: 1                      # Number of nodes
    tasks_per_node: 1             # Tasks per node
    cpus_per_task: 8              # CPUs per task
    gpus_per_node: 0              # GPUs per node
```

**Common Parameters** (from submitit):

- **`slurm_partition`**: SLURM partition/queue name
- **`timeout_min`**: Job timeout in minutes
- **`mem_gb`**: Memory allocation per node in gigabytes
- **`nodes`**: Number of compute nodes
- **`tasks_per_node`**: Number of MPI tasks per node
- **`cpus_per_task`**: Number of CPU cores per task
- **`gpus_per_node`**: Number of GPUs per node
- **`slurm_account`**: SLURM account to charge (if required)
- **`slurm_qos`**: Quality of Service specification

For a complete list of available parameters, refer to the [submitit documentation](https://github.com/facebookincubator/submitit).

## GitHub Personal Access Token

The grader requires a GitHub Personal Access Token (PAT) with appropriate permissions to access GitHub Classroom data and clone student repositories.

### Creating a PAT

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate a new token with the following scopes:
   - `repo` (Full control of private repositories)
   - `read:org` (Read organization data)
   - `admin:org` (if managing classroom assignments)

### Providing the PAT

You have two options:

**Option 1: Environment Variable** (Recommended)

```bash
export GH_PAT="github_pat_xxxxx"
uv run main.py
```

Or inline:
```bash
GH_PAT="github_pat_xxxxx" uv run main.py
```

**Option 2: Configuration File**

Add it directly to `grader-config.yaml`:
```yaml
grader:
  github_pat: "github_pat_xxxxx"
```

As shown in [main.py](main.py), the environment variable takes precedence over the config file value:

```python
token = os.getenv("GH_PAT") or config.config.grader.github_pat
```

## Running the Grader

Once configured, run the grader:

```bash
uv run main.py
# or
python main.py
```

The grader will:
1. Read the configuration file
2. For each assignment (unless skipped):
   - Fetch student submissions from GitHub Classroom
   - Clone each student's repository
   - Copy the test script to the repository
   - Execute the test script
   - Parse the output for test results and performance metrics
   - Clean up (unless `preserve_repo_files` is true)
3. Save all results to the `grades_file`

## Setting Up as a Recurrent Task

To run the grader automatically at regular intervals without administrator privileges, you can use `cron` (Linux/macOS) or `systemd` user timers.

### Option 1: Using Cron

1. Open your crontab for editing:
   ```bash
   crontab -e
   ```

2. Add a cron job to run the grader. Examples:

   **Run every day at 2 AM:**
   ```cron
   0 2 * * * cd /path/to/grader && /usr/bin/uv run main.py >> /path/to/grader/cron.log 2>&1
   ```

   **Run every 6 hours:**
   ```cron
   0 */6 * * * cd /path/to/grader && /usr/bin/uv run main.py >> /path/to/grader/cron.log 2>&1
   ```

   **Run every Monday at 9 AM:**
   ```cron
   0 9 * * 1 cd /path/to/grader && /usr/bin/uv run main.py >> /path/to/grader/cron.log 2>&1
   ```

3. Make sure to:
   - Use absolute paths for both the grader directory and the `uv` executable
   - Export the `GH_PAT` environment variable in the cron job if not using the config file:
     ```cron
     0 2 * * * cd /path/to/grader && GH_PAT="github_pat_xxxxx" /usr/bin/uv run main.py >> /path/to/grader/cron.log 2>&1
     ```

### Option 2: Using Systemd User Timer

Systemd user timers don't require root privileges and offer more control.

1. Create a service file at `~/.config/systemd/user/grader.service`:

   ```ini
   [Unit]
   Description=GitHub Classroom Autograder
   
   [Service]
   Type=oneshot
   WorkingDirectory=/path/to/grader
   Environment="GH_PAT=github_pat_xxxxx"
   ExecStart=/usr/bin/uv run main.py
   
   [Install]
   WantedBy=default.target
   ```

2. Create a timer file at `~/.config/systemd/user/grader.timer`:

   ```ini
   [Unit]
   Description=Run GitHub Classroom Autograder daily
   
   [Timer]
   OnCalendar=daily
   Persistent=true
   
   [Install]
   WantedBy=timers.target
   ```

3. Enable and start the timer:

   ```bash
   systemctl --user daemon-reload
   systemctl --user enable grader.timer
   systemctl --user start grader.timer
   ```

4. Check timer status:

   ```bash
   systemctl --user list-timers
   systemctl --user status grader.timer
   ```

**Timer Schedule Examples:**

- `OnCalendar=daily` - Run once per day at midnight
- `OnCalendar=*-*-* 02:00:00` - Run daily at 2 AM
- `OnCalendar=Mon *-*-* 09:00:00` - Run every Monday at 9 AM
- `OnCalendar=*-*-* 00/6:00:00` - Run every 6 hours

## Test Script Format

Your test scripts must output results in the following JSON format on the **last line** of stdout:

```json
{"passed": 12, "total": 12, "times": [442.44, 664.42, 886.58]}
```

**Required Fields:**

- **`passed`**: Number of tests passed (integer)
- **`total`**: Total number of tests (integer)
- **`times`**: Array of runtime measurements in milliseconds (array of floats)

**Example Test Script Output:**

```bash
#!/bin/bash
# ... test execution ...
echo "Test 1: PASSED"
echo "Test 2: PASSED"
echo "Test 3: FAILED"

# Last line must be JSON
echo '{"passed": 2, "total": 3, "times": [123.45, 234.56, 345.67]}'
```

## Output Format

The grader produces a JSON file (specified in `grades_file`) with the following structure:

```json
{
  "assignment-name": [
    {
      "name": "Student Name",
      "commit_hash": "abc1234",
      "status": "graded",
      "error": "",
      "stdout": "Test output...",
      "avg_runtime": 123.456,
      "data": {
        "passed": 10,
        "total": 10,
        "times": [100.0, 120.5, 150.3]
      }
    }
  ]
}
```

**Field Descriptions:**

- **`name`**: Student name(s) associated with the submission
- **`commit_hash`**: Git commit hash (first 7 characters) of the graded submission
- **`status`**: Grading status (`"graded"` or `"error"`)
- **`error`**: Error message if status is `"error"`, empty otherwise
- **`stdout`**: Complete output from the test script
- **`avg_runtime`**: Average of all runtime values from the `times` array (in milliseconds)
- **`data`**: The parsed JSON output from the test script (see [Test Script Format](#test-script-format))

---

## Troubleshooting

**Issue: "GitHub Personal Access Token (PAT) not provided"**
- Make sure you've set the `GH_PAT` environment variable or added `github_pat` to the config file
- Verify the token has the correct permissions

**Issue: "working_dir does not exist"**
- Create the directory specified in `working_dir` before running: `mkdir -p /tmp/grader`

**Issue: Test script not found**
- Verify the `test_script_path` points to an existing file
- Use absolute paths or ensure relative paths are correct from the grader directory

**Issue: Test results not showing in output**
- Ensure your test script outputs valid JSON on its last line
- Check that the JSON format matches exactly: `{"passed": X, "total": Y, "times": [...]}`
- Review test script stdout in the leaderboard JSON for debugging

**Issue: Cron job not running**
- Check cron logs: `grep CRON /var/log/syslog` (Linux) or `log show --predicate 'process == "cron"' --last 1h` (macOS)
- Verify absolute paths in the crontab entry
- Ensure the cron output log file is writable

---

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

Copyright (C) 2026

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.


