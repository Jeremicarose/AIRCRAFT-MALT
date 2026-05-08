CONTRACT_NAME := receiver-registry
TARGET := riscv64imac-unknown-none-elf

.PHONY: help test check build clean

help:
	@echo "Available targets:"
	@echo "  make test   - run Rust unit tests"
	@echo "  make check  - type-check contract for the CKB target"
	@echo "  make build  - build optimized CKB contract binary"
	@echo "  make clean  - remove build artifacts"

test:
	cargo test

check:
	cargo check --target $(TARGET)

build:
	cargo build --release --target $(TARGET)

clean:
	cargo clean
