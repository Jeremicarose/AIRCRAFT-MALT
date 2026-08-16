CONTRACT_NAME := receiver-registry
TARGET := riscv64imac-unknown-none-elf

.PHONY: help test check build clean

help:
	@echo "Available targets:"
	@echo "  make test   - run Rust unit tests"
	@echo "  make check  - type-check contract for the CKB target"
	@echo "  make build  - build optimized CKB contract binary"
	@echo "  make clean  - remove build artifacts"

test: build
	cargo test --locked --lib --test lifecycle

check:
	cargo check --locked --target $(TARGET) --features contract-bin --bin $(CONTRACT_NAME)

build:
	cargo build --locked --release --target $(TARGET) --features contract-bin

clean:
	cargo clean
