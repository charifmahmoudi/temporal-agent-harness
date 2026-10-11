"""Bounded development comparison, not Temporal replay or source soundness proof."""
import argparse
import ast
import asyncio
from dataclasses import asdict, dataclass, replace
import hashlib
from itertools import accumulate, product
import json
from pathlib import Path
from types import SimpleNamespace

from prepare_cancellation_variant import corrected, SOURCE

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / 'research/evaluation/encoding-comparison-protocol.json'
PROTOCOL_SHA = '7577d5f38f7fc7cc87895aa4924b2f3546242ce24d5d7dc845b249043b081d63'
PROTOCOL_COMMIT = 'c47873ec31c1916c641cdee3074dd5b4bb1d8e58'
OUTPUT = ROOT / 'research/evaluation/encoding-comparison-results.json'
PATCH = 'approval-caller-cancel-v1'
MARKER = 'patch:' + PATCH


def sha(data):
    return hashlib.sha256(data).hexdigest()


def protocol():
    data = PROTOCOL.read_bytes()
    if sha(data) != PROTOCOL_SHA:
        raise ValueError('Frozen protocol changed; version it instead of rewriting it')
    return json.loads(data)


@dataclass(frozen=True)
class Case:
    variant: str
    schedule: tuple
    child: str
    approved: bool
    context: str
    signature: str
    exclusion: str = ''


@dataclass(frozen=True)
class Result:
    outcome: str
    patch_calls: int
    commands: tuple


def supported(case, p):
    return (
        not case.exclusion
        and case.variant in p['variants']
        and len(case.schedule) <= p['maximum_schedule_length']
        and all(e in p['schedule_alphabet'] for e in case.schedule)
        and case.child in p['child_outcomes']
        and type(case.approved) is bool
        and case.context in {c['name'] for c in p['contexts']}
        and case.signature in p['activity_signatures']
    )


def explicit(case, context, p):
    """Hand-authored operational reference; distinct from executed helper code."""
    if not supported(case, p):
        return None
    pc, count, calls, commands = 'await_child', 0, 0, []
    event_cursor = 0
    while pc != 'done':
        if pc == 'await_child':
            if event_cursor < len(case.schedule):
                event = case.schedule[event_cursor]
                event_cursor += 1
                count = count + 1 if event == 'cancel' else max(0, count - 1)
            else:
                # The three admitted completion categories all settle the catch.
                pc = 'guard'
        elif pc == 'guard':
            if case.variant == 'B' or count == 0:
                pc = 'gate'
            elif case.variant == 'C' or not context['workflow']:
                outcome, pc = 'cancelled', 'done'
            else:
                pc = 'patch'
        elif pc == 'patch':
            calls += 1
            if context['memo'] is not None:
                active = context['memo']
            else:
                active = context['notified'] if context['replay'] else context['activation']
                if active:
                    commands.append(MARKER)
            if active:
                outcome, pc = 'cancelled', 'done'
            else:
                pc = 'gate'
        elif pc == 'gate':
            if case.approved:
                pc = 'dispatch'
            else:
                outcome, pc = 'denied', 'done'
        elif pc == 'dispatch':
            commands.append(case.signature)
            outcome, pc = 'scheduled', 'done'
        else:
            raise AssertionError(pc)
    return Result(outcome, calls, tuple(commands))


def helper_sources():
    baseline = (ROOT / SOURCE).read_text()
    fixed = corrected(baseline)
    anchor = 'if caller is not None and caller.cancelling():'
    if fixed.count(anchor) != 1:
        raise ValueError('Guard drift')
    versioned = fixed.replace(anchor,
        'if caller is not None and caller.cancelling() and (\n'
        f'        not workflow.in_workflow() or workflow.patched("{PATCH}")\n'
        '    ):')
    return {'B': baseline, 'C': fixed, 'V': versioned}


def compile_helper(source):
    nodes = [n for n in ast.parse(source).body
             if isinstance(n, ast.AsyncFunctionDef) and n.name == '_cancel_and_settle']
    if len(nodes) != 1:
        raise ValueError('Expected exactly one top-level helper')
    # Body/control structure are retained; annotations are postponed to avoid imports.
    module = ast.Module(body=[ast.ImportFrom(module='__future__',
        names=[ast.alias(name='annotations')], level=0), nodes[0]], type_ignores=[])
    ast.fix_missing_locations(module)
    return compile(module, '<source-helper>', 'exec')


class Caller:
    def __init__(self):
        self.count = 0

    def cancelling(self):
        return self.count

    def cancel(self):
        self.count += 1

    def uncancel(self):
        if self.count:
            self.count -= 1


class Child:
    """Declared await adapter; this does not simulate asyncio's scheduler."""
    def __init__(self, outcome):
        self.outcome = outcome
        self.cancel_requests = 0

    def cancel(self):
        self.cancel_requests += 1

    def __await__(self):
        yield 'cleanup-boundary'
        if self.outcome == 'error':
            raise ValueError('scripted child exception')
        if self.outcome == 'cancel':
            raise asyncio.CancelledError
        return None


class WorkflowAdapter:
    """Manually specified SDK interface contract, not imported SDK execution."""
    def __init__(self, context):
        self.context = context
        self.commands = []
        self.calls = 0

    def in_workflow(self):
        return self.context['workflow']

    def patched(self, patch_id):
        if patch_id != PATCH:
            raise ValueError('Unexpected patch identity')
        self.calls += 1
        c = self.context
        if isinstance(c['memo'], bool):
            return c['memo']
        if c['replay']:
            answer = c['notified']
        else:
            answer = c['activation']
        if answer:
            self.commands.append('patch:' + patch_id)
        return answer


def merged(case, context, p, codes):
    """Conventional version dispatch + actual helper + explicit environment prefix."""
    if not supported(case, p):
        return None
    caller, child, workflow = Caller(), Child(case.child), WorkflowAdapter(context)
    namespace = {'asyncio': SimpleNamespace(current_task=lambda: caller,
        CancelledError=asyncio.CancelledError), 'workflow': workflow}
    exec(codes[case.variant], namespace)
    coroutine = namespace['_cancel_and_settle'](child)
    try:
        if coroutine.send(None) != 'cleanup-boundary':
            raise AssertionError('Source helper no longer reaches expected suspension')
        for operation in case.schedule:
            getattr(caller, operation)()
        try:
            coroutine.send(None)
        except StopIteration:
            if case.approved:
                workflow.commands.append(case.signature)
                outcome = 'scheduled'
            else:
                outcome = 'denied'
        except asyncio.CancelledError:
            outcome = 'cancelled'
        else:
            raise AssertionError('Unexpected second suspension')
    finally:
        coroutine.close()
    if child.cancel_requests != 1:
        raise AssertionError('Source helper child cancellation changed')
    return Result(outcome, workflow.calls, tuple(workflow.commands))


def boundary_count(schedule):
    # Reflected prefix sum, independently of the operational event loop.
    partials = [0, *accumulate(1 if op == 'cancel' else -1 for op in schedule)]
    return partials[-1] - min(partials)


def reduced(case, context, p, *, mutant=''):
    """Hand-derived suffix formula; observation map is not inferred from source."""
    if not supported(case, p):
        return None
    k = boundary_count(case.schedule) > 0
    if mutant == 'boolean_prefix':
        k = bool(case.schedule) and case.schedule[-1] == 'cancel'
    reached = case.variant == 'V' and context['workflow'] and k
    if mutant == 'unconditional_patch':
        reached = case.variant == 'V' and context['workflow']
    active = (context['memo'] if context['memo'] is not None else
              context['notified'] if context['replay'] else context['activation'])
    if mutant == 'fresh_always_on' and not context['replay'] and context['memo'] is None:
        active = True
    stop = k and (case.variant == 'C' or case.variant == 'V' and
                  (not context['workflow'] or active))
    marker = (MARKER,) if reached and active and context['memo'] is None else ()
    dispatch = case.approved and not stop
    return Result('cancelled' if stop else 'scheduled' if dispatch else 'denied',
                  int(reached), marker + ((case.signature,) if dispatch else ()))


def cursor_match(actual, expected):
    cursor = 0
    for symbol in actual:
        if cursor == len(expected) or symbol != expected[cursor]:
            return False
        cursor += 1
    return cursor == len(expected)


def kind_only_match(actual, expected):
    return [s.split(':')[0] for s in actual] == [s.split(':')[0] for s in expected]


def cases(p):
    schedules = [word for length in range(p['maximum_schedule_length'] + 1)
                 for word in product(p['schedule_alphabet'], repeat=length)]
    for v, s, child, approved, c, signature in product(p['variants'], schedules,
            p['child_outcomes'], p['approved'], p['contexts'], p['activity_signatures']):
        yield Case(v, s, child, approved, c['name'], signature)


def run():
    p = protocol()
    contexts = {c['name']: c for c in p['contexts']}
    sources = helper_sources()
    codes = {v: compile_helper(s) for v, s in sources.items()}
    transcript = hashlib.sha256()
    disagreements, word_disagreements = [], []
    witnesses = {}
    counts = {name: 0 for name in ('boolean_prefix', 'unconditional_patch', 'fresh_always_on', 'kind_only_match')}
    policy_violations = {v: 0 for v in p['variants']}
    concrete_keys, abstract_keys = set(), set()
    case_count = word_count = 0
    for case in cases(p):
        context = contexts[case.context]
        reference = explicit(case, context, p)
        executable = merged(case, context, p, codes)
        abstraction = reduced(case, context, p)
        case_count += 1
        row = {'case': asdict(case), 'explicit': asdict(reference),
               'merged': asdict(executable), 'reduced': asdict(abstraction)}
        if not reference == executable == abstraction:
            disagreements.append(row)
        transcript.update((json.dumps(row, sort_keys=True) + '\n').encode())
        count = boundary_count(case.schedule)
        # Domain-cardinality comparison at one cut, not visited model-checker states.
        external = (case.variant, case.approved, case.context, case.signature)
        concrete_keys.add((*external, count, case.child))
        abstract_keys.add((*external, count > 0))
        if context['workflow'] and not context['replay'] and count > 0 and reference.outcome == 'scheduled':
            policy_violations[case.variant] += 1
        for mutation in ('boolean_prefix', 'unconditional_patch', 'fresh_always_on'):
            wrong = reduced(case, context, p, mutant=mutation)
            if wrong != reference:
                counts[mutation] += 1
                witnesses.setdefault(mutation, {'case': asdict(case),
                    'expected': asdict(reference), 'mutant': asdict(wrong)})
        for word in p['expected_words']:
            word_count += 1
            verdicts = (cursor_match(reference.commands, word),
                        executable.commands == tuple(word), abstraction.commands == tuple(word))
            if len(set(verdicts)) != 1:
                word_disagreements.append({'case': asdict(case), 'expected_word': word, 'verdicts': verdicts})
            transcript.update((json.dumps([word, verdicts], sort_keys=True) + '\n').encode())
            if kind_only_match(reference.commands, word) and not verdicts[0]:
                counts['kind_only_match'] += 1
                witnesses.setdefault('kind_only_match', {'case': asdict(case),
                    'commands': reference.commands, 'expected_word': word})
    exemplar = Case('V', (), 'return', True, 'fresh_on', p['activity_signatures'][0])
    abstentions = []
    for exclusion in p['unsupported_cases']:
        case = replace(exemplar, exclusion=exclusion)
        answers = [explicit(case, contexts[case.context], p),
                   merged(case, contexts[case.context], p, codes),
                   reduced(case, contexts[case.context], p)]
        abstentions.append({'case': exclusion, 'all_arms_unsupported': answers == [None] * 3})
    return {
        'schema': 1, 'protocol_commit': PROTOCOL_COMMIT, 'protocol_sha256': PROTOCOL_SHA,
        'script_sha256': sha(Path(__file__).read_bytes()),
        'source_sha256': {v: sha(s.encode()) for v, s in sources.items()},
        'variant_generator_sha256': sha((ROOT / 'research/scripts/prepare_cancellation_variant.py').read_bytes()),
        'scope': 'declared primitive adapters; exact symbolic word matching; not Temporal core replay',
        'semantic_cases': case_count, 'word_comparison_cells': word_count,
        'disagreements': disagreements, 'word_disagreements': word_disagreements,
        'transcript_sha256': transcript.hexdigest(),
        'negative_control_disagreements': counts, 'negative_control_witnesses': witnesses,
        'fresh_outstanding_cancellation_policy_violations': policy_violations,
        'decision_boundary_domain': {'explicit_keys': len(concrete_keys), 'reduced_keys': len(abstract_keys),
            'meaning': 'unique input keys at the suffix cut; excludes prefix computation; not speedup'},
        'abstention_probes': abstentions,
        'novelty_verdict': 'No advantage in expressiveness or correctness demonstrated; suffix reduction alone is not a new method.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = run()
    if args.check:
        if json.loads(OUTPUT.read_text()) != json.loads(json.dumps(result)):
            raise SystemExit('Encoding comparison drifted; inspect rather than overwrite evidence')
    else:
        OUTPUT.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('semantic_cases', 'word_comparison_cells',
        'negative_control_disagreements', 'decision_boundary_domain', 'novelty_verdict')}, indent=2))
    if result['disagreements'] or result['word_disagreements']:
        raise SystemExit('Comparison falsified: disagreements retained in result file')
    if not all(result['negative_control_disagreements'].values()):
        raise SystemExit('A planned negative control was not detected')
    if not all(x['all_arms_unsupported'] for x in result['abstention_probes']):
        raise SystemExit('An excluded probe was accepted')


if __name__ == '__main__':
    main()
