// Generates the plans used by review/r6/attacks.py with docs/js/nodes.js (as nodes.html does).
const N = require(process.argv[2]);
const mk = (concerns, nodes, extra) => { const p = N.plan({ concerns, nodes, author: extra && extra.author }); p.approved = true; Object.assign(p, extra && extra.set || {}); return p; };
const dx = mk(['depression'], [{ archetype: 'LION' }], { set: { therapist_led: true, dx: ['depression'], intake: { concerns: ['depression'] } } });
const ptsd = mk(['ptsd'], [{ archetype: 'LION' }, { archetype: 'OBSERVER' }], { author: 'therapist', set: { therapist_led: true, intake: { concerns: ['ptsd'] } } });
const dxOwn = mk(['depression'], [{ name: 'Anchor', frames: ['I am steady and I choose my next step'], contexts: ['At my desk'], representation: 'A warm blue lake' }],
  { set: { therapist_led: true, dx: ['depression'], intake: { concerns: ['depression'] } } });
const dxSteady = mk(['depression'], [{ archetype: 'LION', frames: ['I am steady'] }], { set: { therapist_led: true, dx: ['depression'], intake: { concerns: ['depression'] } } });
process.stdout.write(JSON.stringify({ dx, ptsd, dxOwn, dxSteady }));
