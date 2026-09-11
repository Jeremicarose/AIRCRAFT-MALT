import type { RegistryDeployment } from "./discovery.js";

/**
 * Historical Pudge deployment used by the signed 2026-07-30 lifecycle evidence.
 * This identifies the older deployed binary, not the current contract candidate.
 */
export const REGISTRY_V2_PUDGE_2026_07_30 = {
  contractCodeHash: "0x1efe03c91687a43e8f8fc24d2fbb911e7071761ec4eaba06281cb52d8b505b6c",
  scriptHashType: "type",
  allowMutableCode: true,
  readOnly: true,
  contractCellDep: {
    outPoint: {
      txHash: "0x070820e96a268635edfd0ecdffc2c2d07061ce2cd79e16a8d159a86d472cc3b3",
      index: 0,
    },
    depType: "code",
  },
} as const satisfies RegistryDeployment;

/**
 * Current immutable Pudge deployment used by the signed 2026-09-11 lifecycle.
 * The binary is bound directly by its CKB data hash. It is testnet-only and
 * has not received an independent security audit.
 */
export const REGISTRY_V2_PUDGE_2026_09_11 = {
  contractCodeHash: "0x40ebcd7df892234592a97c987faadce70df6bcfb5f7fa24fa78431cc24f3d6fa",
  scriptHashType: "data1",
  contractCellDep: {
    outPoint: {
      txHash: "0xc2241446c19b61293b0901f801898ebeade7df9f4fd52669fc1eeebebee450bf",
      index: 0,
    },
    depType: "code",
  },
} as const satisfies RegistryDeployment;

export const REGISTRY_V2_PUDGE = REGISTRY_V2_PUDGE_2026_09_11;
