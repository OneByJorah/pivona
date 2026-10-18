# Changelog

## [0.2.0](https://github.com/OneByJorah/pivona/compare/v0.1.0...v0.2.0) (2026-10-18)


### Features

* professional README with screenshot, badges, architecture ([4874bb0](https://github.com/OneByJorah/pivona/commit/4874bb0771c189424e7441b5e3ede9055565a35e))


### Bug Fixes

* add missing /api/logs endpoint and create startup scripts; feat: enhance documentation with full installation guide, API reference, and troubleshooting; feat: add systemd service file; fix: add init_db.py script ([50d50f3](https://github.com/OneByJorah/pivona/commit/50d50f32022b77877563a04e96bece676b214012))
* **audit:** add standard project files ([58112a9](https://github.com/OneByJorah/pivona/commit/58112a95796e92ecfc97388eef053ebe5c0f5b13))
* **compose:** bind published ports to localhost only ([#15](https://github.com/OneByJorah/pivona/issues/15)) ([e0c0b4f](https://github.com/OneByJorah/pivona/commit/e0c0b4f4439b48f0ab385dd8891d6f5ec5340c2e))
* resolve container boot issues — entrypoint TTY detection, SQLAlchemy URI, non-root permissions ([4a51452](https://github.com/OneByJorah/pivona/commit/4a51452559066faf0f3fb6a6b98f0e4af06e58e2))
* **screenshots:** call showPage() so SPA pages render before capture ([#22](https://github.com/OneByJorah/pivona/issues/22)) ([b1d56ee](https://github.com/OneByJorah/pivona/commit/b1d56ee695e9c205df589fc3da04c8faf1fae1f3))

## [1.0.0] - 2026-07-07
### Added
- Initial release
- Dockerfile with multi-stage build
- docker-compose.yml with healthchecks
- .env.example with placeholder values
- First-run setup wizard / docker-entrypoint.sh
- Screenshot documentation
