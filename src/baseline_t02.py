"""T02 required baseline: one global Laplacian threshold fitted on dev."""
from .pipeline import load
from . import t02


def run(ctx):
    if ctx.track != "t02":
        raise ValueError("baseline_t02 requires --track t02")
    data = load(ctx)
    scored = t02.process(ctx, data["images"], baseline=True)
    queue = t02.rank(ctx, scored)
    t02.finish(ctx, scored, queue)
