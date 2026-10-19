import asyncio, json, time
from ckb_registry.discovery import CKBConfig, CKBPeerDiscovery
async def main():
    discovery = CKBPeerDiscovery(CKBConfig(receiver_registry_type_hash="0x40ebcd7df892234592a97c987faadce70df6bcfb5f7fa24fa78431cc24f3d6fa"))
    started = time.monotonic()
    await discovery.initialize()
    receivers = await discovery.discover_peers(include_inactive=True, include_revoked=True)
    print(json.dumps({"receivers_verified_against_node": len(receivers), "revoked": sum(item.status == "revoked" for item in receivers), "quarantined": len(discovery.quarantined_identities), "duration_seconds": time.monotonic()-started, "signed_transactions": 0}))
asyncio.run(main())
