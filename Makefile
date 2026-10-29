# A wrapper to build pp-code-metrics docker
#
# __author__: tuan t. pham

DOCKER_NAME ?=neofob/pp-code-metrics
DOCKER_TAG ?=latest

docker:
	docker build -t $(DOCKER_NAME):$(DOCKER_TAG) .
	# or, docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

pause:
	docker-compose pause

test:
	python -m pytest tests/
	python -m py_compile get_metrics.py 
	ruff check get_metrics.py
