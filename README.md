# QEC Data Generation for Neural-Network Decoders
This repository contains the code used to generate quantum error-correction (QEC) data for training neural-network–based decoders.

tools.py – Utility functions for creating and processing .b8 result files.

noise.py and surface_code.py – Modules for generating noisy surface-code circuits.

## Generating Training Data

Example scripts demonstrating how to generate datasets can be found in:

- `generate_test_data.py`
- `generate_training_data.py`

These provide reference workflows for building circuits, simulating noise, and exporting data in the required format.

