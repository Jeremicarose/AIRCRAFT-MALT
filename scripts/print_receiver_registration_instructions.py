#!/usr/bin/env python3
"""
Print the manual receiver-registration steps for the current repository setup.
"""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    record_json = Path("deploy/receiver-registry-record.json")
    record_hex = Path("deploy/receiver-registry-record.hex")

    print("Receiver registration checklist")
    print("=" * 40)
    print("1. Generate the canonical record:")
    print("   python3 scripts/generate_receiver_registry_record.py ...")
    print()
    print("2. Confirm these files exist:")
    print(f"   - {record_json}")
    print(f"   - {record_hex}")
    print()
    print("3. Use the newly deployed Registry V2 contract code hash and outpoint.")
    print()
    print("4. Build a cell transaction that:")
    print("   - uses your deployer lock script as owner")
    print("   - sets type.code_hash to the receiver-registry type hash")
    print("   - sets type.hash_type to 'type'")
    print("   - sets type.args to the 32-byte Type ID derived from the first input")
    print("   - never reuses a Receiver Identity for another receiver lifecycle")
    print("   - writes the generated hex payload as output data")
    print()
    print("5. Run apply_receiver_type_script.py after the first input exists.")
    print("6. After registration, restart mlat-processor and query /api/receivers")


if __name__ == "__main__":
    main()
