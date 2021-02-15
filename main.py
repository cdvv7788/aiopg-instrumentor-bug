import asyncio

from aiohttp import web
import aiopg
from opentelemetry import trace
from opentelemetry.exporter import jaeger
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
from opentelemetry.instrumentation.aiopg import AiopgInstrumentor

jaeger_exporter = jaeger.JaegerSpanExporter(
        service_name="test", agent_host_name="127.0.0.1", agent_port=5775
    )

trace_provider = TracerProvider()
trace_provider.add_span_processor(BatchExportSpanProcessor(jaeger_exporter))
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)

AiopgInstrumentor().instrument()

dsn = "dbname=test user=postgres password=postgres host=127.0.0.1"

async def init_pg(app):
    pool = await aiopg.create_pool(dsn)
    app["pool"] = pool


async def handle(request):
    async with request.app["pool"].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1")
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)

app = web.Application()
app.add_routes([web.get('/', handle),
                web.get('/{name}', handle)])
app.on_startup.append(init_pg)

if __name__ == '__main__':
    web.run_app(app, port=4000)

