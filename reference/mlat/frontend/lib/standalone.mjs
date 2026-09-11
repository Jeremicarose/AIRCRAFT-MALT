import path from 'node:path';
import { access, cp, mkdir, mkdtemp, readFile, rm } from 'node:fs/promises';

export const PRODUCTION_DIST_DIR = '.next-production';
export const RUNTIME_DIR = '.next-runtime';

/**
 * Resolve the paths produced by Next.js when output: 'standalone' is enabled.
 * The tracing root is the repository root, so the generated server keeps the
 * frontend's repository-relative directory inside the standalone output.
 */
export function resolveStandalonePaths({
  projectRoot,
  tracingRoot = path.resolve(projectRoot, '../../..'),
  distDir = process.env.NEXT_DIST_DIR || PRODUCTION_DIST_DIR,
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
    relativeProjectPath,
    staticSource: path.join(resolvedDistDir, 'static'),
    publicSource: path.join(resolvedProjectRoot, 'public'),
    standaloneRoot,
    standaloneProjectRoot,
    standaloneStatic: path.join(standaloneProjectRoot, path.basename(resolvedDistDir), 'static'),
    standalonePublic: path.join(standaloneProjectRoot, 'public'),
    server: path.join(standaloneProjectRoot, 'server.js'),
  };
}

async function validateStandaloneBuild(paths) {
  if (!(await exists(paths.server))) {
    throw new Error(`Standalone server not found at ${paths.server}. Run npm run build first.`);
  }
  if (!(await exists(paths.staticSource))) {
    throw new Error(`Next static assets not found at ${paths.staticSource}. Run npm run build first.`);
  }
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

  await validateStandaloneBuild(paths);

  await cp(paths.staticSource, paths.standaloneStatic, { recursive: true });
  if (await exists(paths.publicSource)) {
    await cp(paths.publicSource, paths.standalonePublic, { recursive: true });
  }

  return paths;
}

/**
 * Copy a complete build into a unique runtime directory before startup. This
 * prevents a later build from replacing hashed assets beneath a running server.
 */
export async function stageStandaloneBuild(options) {
  const source = resolveStandalonePaths(options);
  await validateStandaloneBuild(source);

  const buildIdPath = path.join(source.distDir, 'BUILD_ID');
  const buildId = (await readFile(buildIdPath, 'utf8')).trim();
  if (!buildId) {
    throw new Error(`Next build ID is empty at ${buildIdPath}. Run npm run build again.`);
  }

  const runtimeBase = path.join(source.projectRoot, RUNTIME_DIR);
  await mkdir(runtimeBase, { recursive: true });
  const runtimeContainer = await mkdtemp(path.join(runtimeBase, `${buildId}-`));
  const runtimeRoot = path.join(runtimeContainer, 'bundle');

  try {
    await cp(source.standaloneRoot, runtimeRoot, { recursive: true });

    const standaloneProjectRoot = path.join(runtimeRoot, source.relativeProjectPath);
    const standaloneDistDir = path.join(standaloneProjectRoot, path.basename(source.distDir));
    const standaloneStatic = path.join(standaloneDistDir, 'static');
    const standalonePublic = path.join(standaloneProjectRoot, 'public');

    await cp(source.staticSource, standaloneStatic, { recursive: true });
    if (await exists(source.publicSource)) {
      await cp(source.publicSource, standalonePublic, { recursive: true });
    }

    const buildIdAfterCopy = (await readFile(buildIdPath, 'utf8')).trim();
    if (buildIdAfterCopy !== buildId) {
      throw new Error('The production build changed while it was being staged. Run npm run start again.');
    }

    return {
      ...source,
      runtimeContainer,
      runtimeRoot,
      standaloneRoot: runtimeRoot,
      standaloneProjectRoot,
      standaloneDistDir,
      standaloneStatic,
      standalonePublic,
      server: path.join(standaloneProjectRoot, 'server.js'),
    };
  } catch (error) {
    await rm(runtimeContainer, { recursive: true, force: true });
    throw error;
  }
}
