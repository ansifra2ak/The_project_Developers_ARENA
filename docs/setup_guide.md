# Setup and Execution Guide

## Prerequisites

- Python 3 with compatible scientific libraries
- Visual Studio Code
- Python and Jupyter extensions
- Git

## Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Open and Execute a Project

1. Open the individual project folder in VS Code.
2. Locate its Jupyter notebook.
3. Select the intended Python environment/kernel.
4. Execute the project's analysis code.
5. Inspect the output and check for exceptions.
6. Review the generated CSV, PNG and PDF files.
7. Verify that reports reflect the computed results.

## Troubleshooting

If you see ModuleNotFoundError, check that the
notebook kernel matches the environment where
the required packages were installed.

Do not upload virtual environment directories
to GitHub.

## Reproducibility

The notebooks generate or load datasets and may
overwrite their generated output files when rerun.
Preserve copies of final reports as needed.
