# C4 Diagram Generator for Python Modules

## Overview

`c4_maker.py` is a Python script designed to generate C4 model diagrams from Python code. It uses the OpenAI API to analyze source code and generate annotations for both components and relationships within the code. These annotations are then used to create a PlantUML diagram representing the system's architecture.

## Features

- **Code Analysis**: Analyzes Python modules to identify components and their relationships.
- **C4 Model Generation**: Generates C4 model diagrams using PlantUML with annotations derived from the source code.
- **OpenAI Integration**: Utilizes OpenAI's API to interpret and annotate source code.

## Prerequisites

Before you run the script, ensure you have the following installed:
- Python 3.6 or higher
- `openai` Python library
- `dotenv` Python library
- An active OpenAI API key set in a `.env` file

## Installation

Install directly from source:

```bash
pip install .
