import path from 'node:path';
import { access, cp } from 'node:fs/promises';

/**
 * Resolve the paths produced by Next.js when output: 'standalone' is enabled.
 * The tracing root is the repository root, so the generated server keeps the
 * frontend's repository-relative directory inside .next/standalone.
 */
export function resolveStandalonePaths({
  projectRoot,
  tracingRoot = path.resolve(projectRoot, '../../..'),
  distDir = process.env.NEXT_DIST_DIR || '.next',
} = {}) {
  if (!projectRoot) {
    throw new Error('projectRoot is required');
  }

  const resolvedProjectRoot = path.resolve(projectRoot);
  const resolvedTracingRoot = path.resolve(tracingRoot);
  const resolvedDistDir = path.resolve(resolvedProjectRoot, distDir);
  const relativeProjectPath = path.relative(resolvedTracingRoot, resolvedProjectRoot);

  if (!relativeProjectPath || relativeProjectPath.startsWith('..') || path.isAbsolute(relativeProjectPath)) {
    throw new Error(`projectRoot must be inside tracingRoot: ${resolvedProjectRoot}`);
  }

  const standaloneRoot = path.join(resolvedDistDir, 'standalone');
  const standaloneProjectRoot = path.join(standaloneRoot, relativeProjectPath);

  return {
    projectRoot: resolvedProjectRoot,
    distDir: resolvedDistDir,
    staticSource: path.join(resolvedDistDir, 'static'),
    publicSource: path.join(resolvedProjectRoot, 'public'),
    standaloneRoot,
    standaloneProjectRoot,
    standaloneStatic: path.join(standaloneProjectRoot, path.basename(resolvedDistDir), 'static'),
    standalonePublic: path.join(standaloneProjectRoot, 'public'),
    server: path.join(standaloneProjectRoot, 'server.js'),
  };
}

async function exists(candidate) {
  try {
    await access(candidate);
    return true;
  } catch {
    return false;
  }
}

/**
 * Next.js does not copy public or .next/static into a standalone bundle.
 * Copy them beside the traced server before it is started.
 */
export async function prepareStandaloneAssets(options) {
  const paths = resolveStandalonePaths(options);

  if (!(await exists(paths.server))) {
    throw new Error(`Standalone server not found at ${paths.server}. Run npm run build first.`);
  }
  if (!(await exists(paths.staticSource))) {
    throw new Error(`Next static assets not found at ${paths.staticSource}. Run npm run build first.`);
  }

  await cp(paths.staticSource, paths.standaloneStatic, { recursive: true });
  if (await exists(paths.publicSource)) {
    await cp(paths.publicSource, paths.standalonePublic, { recursive: true });
  }

  return paths;
}
