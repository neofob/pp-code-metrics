# A wrapper to build pp-code-metrics docker
#
# __author__: tuan t. pham

DOCKER_NAME ?=neofob/pp-code-metrics
DOCKER_TAG ?=latest

docker:
	docker build -t $(DOCKER_NAME):$(DOCKER_TAG) .

up:
	docker-compose up -d

down:
	docker-compose down

pause:
	docker-compose pause
