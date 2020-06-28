#!/bin/bash

app_name="aeye_typer"          # Docker image name

nvidia-docker build -t $app_name .  # Start the Docker image build