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
