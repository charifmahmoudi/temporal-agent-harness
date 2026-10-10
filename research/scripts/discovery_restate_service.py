"""Small service fixture; selected variant is fixed for each endpoint process."""
import asyncio
from datetime import timedelta
import json
import os
from pathlib import Path
import restate
from hypercorn.asyncio import serve
from hypercorn.config import Config

service = restate.Workflow('DiscoveryRecovery')
OUT = Path(os.environ['DISCOVERY_OUTPUT'])
BROKEN = os.environ.get('DISCOVERY_BROKEN') == '1'


def record(key: str, kind: str) -> str:
    with (OUT / 'ledger.jsonl').open('a') as f:
        f.write(json.dumps({'key': key, 'kind': kind}) + '\n')
    return kind


@service.main()
async def run(ctx: restate.WorkflowContext, key: str):
    if BROKEN:
        await ctx.sleep(timedelta(days=1))
    await ctx.run_typed('effect', record, key=key, kind='effect')
    try:
        await ctx.promise('hold').value()
    except restate.TerminalError:
        await ctx.run_typed('cleanup', record, key=key, kind='cleanup')
        raise


@service.handler()
async def wake(ctx: restate.WorkflowSharedContext):
    # A shared handler need not release the blocked main invocation.
    return 'reachable'


if __name__ == '__main__':
    config = Config()
    config.bind = ['127.0.0.1:9080']
    asyncio.run(serve(restate.app(services=[service]), config))
