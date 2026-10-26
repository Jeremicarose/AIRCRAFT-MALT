/** Browser-local learning milestones. They never represent system readiness. */
export const missions = [
  { id: 'source', title: 'Know your source', badge: 'Source reader', points: 25, href: '/app/guide#source-challenge', action: 'Start the challenge', detail: 'Learn what a Registry record can and cannot tell you.', requirement: 'Answer the source question below.' },
  { id: 'receiver', title: 'Meet a receiver', badge: 'Receiver explorer', points: 50, href: '/app/receivers', action: 'Inspect a receiver', detail: 'Select a receiver and compare its identity, feed status, and clock qualification.', requirement: 'Select an available receiver row. Synthetic and historical receivers count for learning.' },
  { id: 'pipeline', title: 'Follow the signal', badge: 'Pipeline tracer', points: 50, href: '/app/pipeline', action: 'Trace the pipeline', detail: 'Choose a processing stage and inspect its evidence and next action.', requirement: 'Select a stage returned by the pipeline service.' },
  { id: 'benchmark', title: 'Read beyond the score', badge: 'Benchmark reader', points: 50, href: '/app/benchmark#benchmark-challenge', action: 'Explore accuracy', detail: 'Compare solver fit with actual position error, including rejected events.', requirement: 'Read the available benchmark and answer its interpretation question.' },
  { id: 'replay', title: 'Investigate a recorded event', badge: 'Replay investigator', points: 75, href: '/app/replay', action: 'Explore a replay', detail: 'Follow a recorded event to the solver stage. Rejections are useful evidence too.', requirement: 'Requires the historical replay service. Select the solver stage of a recorded event.' },
  { id: 'diagnostics', title: 'Prepare a useful report', badge: 'Diagnostic contributor', points: 50, href: '/app/environment', action: 'Export diagnostics', detail: 'Save the sanitized diagnostic report so a problem can be reproduced.', requirement: 'The diagnostic endpoint must return a valid report before this mission counts.' },
] as const;

export type MissionId = typeof missions[number]['id'];
export const totalMissionPoints = missions.reduce((sum, mission) => sum + mission.points, 0);

export function validCompletions(value: unknown): MissionId[] {
  if (!Array.isArray(value)) return [];
  return missions.filter((mission) => value.includes(mission.id)).map((mission) => mission.id);
}

export function missionProgress(value: unknown) {
  const completed = validCompletions(value);
  const points = missions.reduce((sum, mission) => sum + (completed.includes(mission.id) ? mission.points : 0), 0);
  const rank = points >= 300 ? 'Console navigator' : points >= 175 ? 'Investigator' : points >= 75 ? 'Explorer' : 'New observer';
  const next = missions.find((mission) => !completed.includes(mission.id));
  return { completed, points, rank, next, percent: Math.round(points / totalMissionPoints * 100) };
}
