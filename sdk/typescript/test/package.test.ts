import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

interface PackageManifest {
  name?: string;
  private?: boolean;
  repository?: {
    url?: string;
    directory?: string;
  };
  publishConfig?: {
    access?: string;
    provenance?: boolean;
    registry?: string;
  };
}

test("package manifest remains ready for a public provenance-backed release", async () => {
  const manifestPath = new URL("../../package.json", import.meta.url);
  const manifest = JSON.parse(await readFile(manifestPath, "utf8")) as PackageManifest;

  assert.equal(manifest.name, "@aircraft-malt/registry-v2");
  assert.notEqual(manifest.private, true);
  assert.equal(
    manifest.repository?.url,
    "git+https://github.com/Jeremicarose/AIRCRAFT-MALT.git",
  );
  assert.equal(manifest.repository?.directory, "sdk/typescript");
  assert.deepEqual(manifest.publishConfig, {
    access: "public",
    provenance: true,
    registry: "https://registry.npmjs.org/",
  });
});
