.PHONY: test lint docker-build-local release-test tag
test:
	uv run pytest tests/
lint:
	ruff check .
docker-build-local:
	docker build -t example/app:local .
release-test:
	bash scripts/release-test/release-image-test.sh $(TAG) $(OLD_TAG)
tag:
	@version=$$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	git tag "v$$version"
