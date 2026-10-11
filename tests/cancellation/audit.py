"""Concrete integrity checks for the study's single-call, single-evaluation probes.

These are observation checks, not properties encoded in Cleanup.tla or a general
multi-call event validator. Event payload schemas are checked separately in tests.
"""
TERMINALS = {
    'auto_approval_evaluation_ended',
    'auto_approval_evaluation_superseded',
    'auto_approval_evaluation_error',
}


def validate_audit(events, tool_id='call'):
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    starts = [e for e in events if e['type'] == 'auto_approval_evaluation_started']
    terminals = [e for e in events if e['type'] in TERMINALS]
    require(len(starts) == 1, 'expected one evaluation start')
    require(len(terminals) == 1, 'expected exactly one evaluation terminal across ended/superseded/error')
    start, terminal = starts[0], terminals[0]
    require(isinstance(start.get('evaluation_id'), str) and bool(start['evaluation_id']),
            'missing evaluation identity')
    require(start['evaluation_id'] == terminal.get('evaluation_id'), 'evaluation identity mismatch')
    require(start.get('evaluator') == terminal.get('evaluator'), 'evaluator identity mismatch')
    require(terminal['type'] == 'auto_approval_evaluation_superseded', 'expected superseded evaluation')
    observed = [*starts, *terminals, *[e for e in events if e['type'] == 'tool_start']]
    require(all(e.get('tool_id') == tool_id for e in observed), 'unexpected call identity')
    require(all(e.get('tool_name') == start.get('tool_name') for e in observed), 'tool name mismatch')
    require(events.index(start) < events.index(terminal), 'evaluation terminal precedes start')
