# Created by: George Araújo (george.gcac@gmail.com)

# ==================================================================
# environment variables
# ------------------------------------------------------------------

DOCKERFILE_CONTEXT = $(PWD)
DOCKERFILE = $(PWD)/Dockerfile
DATA_DIR = $(HOME)/datasets/ai_papers
WORK_DIR = $(PWD)
RUN_STRING = bash start_here.sh

# ==================================================================
# Docker settings
# ------------------------------------------------------------------

CONTAINER_NAME = scrapper-$(USER)-$(shell echo $$STY | cut -d'.' -f2) # use gnu screen name when creating container
CONTAINER_FILE = scrapper-$(USER).tar
HOSTNAME = docker-$(shell hostname)
IMAGE_NAME = $(USER)/ai-papers-scrapper
DATA_PATH = /work/data
WORK_PATH = /work

RUN_CONFIG_STRING = --name $(CONTAINER_NAME) --hostname $(HOSTNAME) --rm -it --dns 8.8.8.8 \
	--userns=host --ipc=host --ulimit memlock=-1 -w $(WORK_PATH) $(IMAGE_NAME):latest
DATA_MOUNT_STRING = --mount type=bind,source=$(DATA_DIR),target=$(DATA_PATH)
WORK_MOUNT_STRING = --mount type=bind,source=$(WORK_DIR),target=$(WORK_PATH)

# ==================================================================
# Make commands
# ------------------------------------------------------------------

# Build image
build:
	docker build \
		--build-arg GROUPID=$(shell id -g) \
		--build-arg GROUPNAME=$(shell id -gn) \
		--build-arg USERID=$(shell id -u) \
		--build-arg USERNAME=$(USER) \
		-f $(DOCKERFILE) \
		--pull --no-cache --force-rm \
		-t $(IMAGE_NAME) \
		$(DOCKERFILE_CONTEXT)


# Remove the image
clean:
	docker rmi $(IMAGE_NAME)


# Load image from file
load:
	docker load -i $(CONTAINER_FILE)


# Kill running container
kill:
	docker kill $(CONTAINER_NAME)


# Run RUN_STRING inside container
run:
	docker run \
		$(WORK_MOUNT_STRING) \
		$(DATA_MOUNT_STRING) \
		$(RUN_CONFIG_STRING) \
		$(RUN_STRING)


# Save image to file
save:
	docker save -o $(CONTAINER_FILE) $(IMAGE_NAME)


# Start container by opening shell
start:
	docker run \
		$(WORK_MOUNT_STRING) \
		$(DATA_MOUNT_STRING) \
		$(RUN_CONFIG_STRING)


# Test image by printing some info
test:
	nvidia-docker run \
		$(RUN_CONFIG_STRING) \
		python -V

