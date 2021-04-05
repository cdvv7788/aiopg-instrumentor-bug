import asyncio

from aiohttp import web
import aiopg
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.aiopg import AiopgInstrumentor

trace_provider = TracerProvider(resource=Resource.create({SERVICE_NAME: "my-service"}))
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)




jaeger_exporter = JaegerExporter(
        agent_host_name="127.0.0.1", agent_port=5775
    )
span_processor = BatchSpanProcessor(jaeger_exporter)

trace.get_tracer_provider().add_span_processor(span_processor)

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

