#!/bin/bash

app_name="fast_aeye_typer"          # Docker image name

nvidia-docker build -t $app_name .  # Start the Docker image build