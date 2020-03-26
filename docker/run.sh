#!/bin/bash

# Runs the docker container given by `app_name` with the applications local
# codebase and data directories mounted, along with the user's local home
# directory mounted.

app_name="fast_aeye_typer"  # Your docker image name


# Set up cmd line args
local_codebase_dir=$1
local_data_dir=$2
local_home_dir=$(echo ~)

# Validate cmd line  args
if [[ -z $local_codebase_dir ]]
then 
  local_codebase_dir="$local_home_dir/repos/$app_name"
  echo "WARN: Missing argument 1 (local codebase path)... Using $local_codebase_dir instead." 
fi

echo "INFO: Mounting $local_codebase_dir at /opt/app/src."

if [[ -z $local_data_dir ]]
then 
  local_data_dir="/data/$app_name"
  echo "WARN: Missing argument 2 (data folder)... Using $local_data_dir instead."
fi

echo "INFO: Mounting $local_data_dir at /opt/app/data."

echo "INFO: Mounting $local_home_dir at /opt/home."

# Set .ssh dir
local_ssh_dir="$local_home_dir/.ssh"

# Allow local x win connections for users in the docker group
xhost +local:docker

# Start a container from the specified docker image with directories mounted
# and a random number appended to the container name
container_name="$app_name"_"$$"

nvidia-docker run --rm -it \
	--name $container_name \
  -v $local_data_dir:/opt/app/data \
  -v $local_codebase_dir:/opt/app/src \
  -v $local_home_dir:/opt/home \
  -v $local_ssh_dir:/root/.ssh \
	-v /tmp/.X11-unix:/tmp/.X11-unix \
	-e DISPLAY \
	--net=host \
  --ipc=host \
	--runtime=nvidia \
	--privileged \
  $app_name