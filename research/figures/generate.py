"""Generate exact, editable SVG illustrations of the documented abstractions.

Figures are explanatory projections, not TLC-generated state graphs. Run from any
working directory. No plotting library or network dependency is needed.
"""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INK, MUTED, BLUE, GREEN, RED = '#15283b', '#516579', '#245bb2', '#167052', '#a52f38'


def figure(name, height, title, description, draw):
    items = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 {height}" role="img" aria-labelledby="title desc">',
             f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
             '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#516579"/></marker></defs>',
             f'<rect width="1120" height="{height}" fill="white"/>',
             '<g font-family="DejaVu Sans,Arial,sans-serif">']

    def text(x, y, label, size=18, color=INK, weight='normal'):
        items.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}">{escape(label)}</text>')

    def box(x, y, w, h, lines, color=BLUE):
        items.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="#f5f8fc" stroke="{color}" stroke-width="2"/>')
        for i, line in enumerate(lines):
            text(x+15, y+29+i*24, line, 17, color if i == 0 else INK, 'bold' if i == 0 else 'normal')

    def arrow(x1, y1, x2, y2, label='', tx=None, ty=None, via=''):
        items.append(f'<path d="M{x1},{y1} {via} L{x2},{y2}" stroke="{MUTED}" stroke-width="2" fill="none" marker-end="url(#arrow)"/>')
        if label:
            text(tx if tx is not None else (x1+x2)/2, ty if ty is not None else (y1+y2)/2-10, label, 15, MUTED)

    text(32, 40, title, 25, weight='bold')
    draw(text, box, arrow)
    items.extend(['</g>', '</svg>'])
    (ROOT / f'{name}.svg').write_text('\n'.join(items)+'\n')


def gate(t, b, a):
    t(32, 78, 'Two state dimensions: decision status and caller phase', 18, MUTED)
    t(32, 121, 'DECISION STATUS', 16, weight='bold')
    b(35, 142, 220, 70, ['pending', 'No accepted resolution'])
    b(445, 142, 220, 70, ['approved', 'First decision retained'], GREEN)
    b(855, 142, 220, 70, ['denied', 'First decision retained'], RED)
    a(255, 160, 445, 160, 'Approve', 302, 148)
    a(145, 212, 965, 212, 'Deny; or close at finalization', 310, 237,
      via='L145,248 L965,248')
    t(32, 275, 'CALLER PHASE', 16, weight='bold')
    b(35, 302, 220, 70, ['evaluating', 'Wait for deciding event'])
    b(445, 302, 220, 70, ['cancelling', 'Evaluator cleanup'])
    b(445, 448, 220, 70, ['gate', 'Wait / finalize outcome'])
    b(855, 395, 220, 70, ['dispatched', 'Approved permission'], GREEN)
    b(855, 540, 220, 70, ['rejected', 'Denied outcome'], RED)
    a(255, 337, 445, 337, 'Consume: superseded', 268, 323)
    a(555, 372, 555, 448, 'Cancelled', 574, 417)
    a(145, 372, 445, 478, 'Consume: ordinary result', 48, 450)
    a(665, 469, 855, 430, 'Finalize: approved', 675, 415)
    a(665, 500, 855, 575, 'Finalize: deny', 679, 570)
    t(32, 630, 'Complete records a verdict; it does not itself resolve the decision.', 17, MUTED)
    t(32, 657, 'Close sets a flag. An unresolved gate is denied only when Finalize executes.', 17, MUTED)


def properties(t, b, a):
    t(32, 80, 'Illustrative valid and faulty traces; fault traces are synthetic controls.', 18, MUTED)
    rows = [
        (120, 'P1 · DecisionStable', ['pending', 'approved', 'approved'], ['pending', 'approved', 'denied'], 'Fault: a later writer replaces the first resolution.'),
        (295, 'P3 · AuthorizedDispatch', ['pending', 'approved', 'dispatched'], ['pending', 'pending', 'dispatched'], 'Fault: dispatch occurs without approval.'),
        (470, 'P7 · CauseBeforeCascade', ['remember(b)', 'publish b', 'publish a'], ['remember(b)', 'publish a', 'publish b'], 'Fault: sibling publication precedes its cause.'),
    ]
    for y, label, good, bad, caption in rows:
        t(32, y, label, 20, weight='bold')
        t(32, y+43, 'VALID', 15, GREEN, 'bold')
        t(32, y+98, 'FAULT', 15, RED, 'bold')
        for j in range(3):
            x=180+j*290
            b(x, y+14, 235, 44, [good[j]], GREEN)
            b(x, y+69, 235, 44, [bad[j]], RED)
            if j < 2:
                a(x+235,y+36,x+290,y+36)
                a(x+235,y+91,x+290,y+91)
        t(180, y+145, caption, 16, MUTED)
    t(32, 675, 'Approval is dispatch permission; these traces do not model committed external effects.', 16, MUTED)


def cascade(t, b, a):
    t(32, 80, 'Calls are registered a then b. The initiating remembered approval is b.', 18, MUTED)
    b(35, 120, 290, 135, ['Initial: same tool', 'a: pending   b: pending', 'allowed: {}', 'history: empty'])
    b(410, 120, 290, 135, ['Remember(b)', 'a: approved   b: approved', 'allowed: {shared}', 'history: b, a'], GREEN)
    b(785, 120, 300, 135, ['Update({})', 'a: approved   b: approved', 'allowed: {}', 'history: b, a'], GREEN)
    a(325,187,410,187)
    a(700,187,785,187)
    t(35, 300, 'Restriction changes eligibility; it does not revoke accepted resolutions.', 19, weight='bold')
    t(35, 359, 'DIFFERENT TOOLS: a is shared; b is other', 17, MUTED, 'bold')
    b(35, 395, 290, 135, ['Initial: different tools', 'a: pending   b: pending', 'allowed: {}', 'history: empty'])
    b(410, 395, 290, 135, ['Remember(a)', 'a: approved   b: pending', 'allowed: {shared}', 'history: a'], GREEN)
    a(325,462,410,462)
    t(745, 430, 'ScopePreserved:', 19, weight='bold')
    t(745, 463, 'the other tool stays gated.', 18)
    t(35, 585, 'Remember / Update are atomic projections of synchronous implementation operations.', 17, MUTED)
    t(35, 614, 'Resolution publication and evaluator cleanup are different stages.', 17, MUTED)


figure('gate', 690, 'Figure 1. Approval model', 'Decision status and caller phase are separate. Cancellation cleanup precedes finalization.', gate)
figure('properties', 710, 'Figure 2. Three safety properties as traces', 'Valid traces preserve decisions, require approval, and publish the initiating cause first.', properties)
figure('cascade', 650, 'Figure 3. Policy-cascade semantics', 'Remember approves eligible pending calls; restriction preserves accepted decisions; different tools remain isolated.', cascade)


def cancellation(t, b, a):
    t(32, 80, 'Accepted approval remains stable; cancellation changes the invocation outcome.', 18, MUTED)
    for y, label, last, color in [(135, 'CURRENT HELPER', 'dispatched', RED),
                                  (360, 'PROPOSED CORRECTION', 'cancelled', GREEN)]:
        t(32, y, label, 18, color, 'bold')
        names = ['accepted approval', 'cleanup waiting', 'caller cancellation', last]
        for i, name in enumerate(names):
            x=35+i*275
            lines=[name, 'status: approved']
            if i==3:
                lines.append('tool starts' if last=='dispatched' else 'no tool start')
            b(x,y+25,235,110,lines,color if i==3 else BLUE)
            if i<3:
                a(x+235,y+80,x+275,y+80)
    t(35, 310, 'Decision stability alone does not imply caller-cancellation respect.', 19, weight='bold')
    t(35, 580, 'Cancellation arrives before dispatch, while the caller awaits evaluator cleanup.', 17, MUTED)
    t(35, 612, 'These are explanatory projections, not complete model-checker state graphs.', 17, MUTED)


figure('cancellation', 650, 'Figure 6. Caller cancellation during cleanup',
       'Current cleanup may swallow caller cancellation and dispatch; proposed correction preserves approval but cancels the invocation.', cancellation)
