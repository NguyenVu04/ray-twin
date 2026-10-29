# docs/architecture/overall.py
import base64
import re

from diagrams import Cluster, Diagram, Edge
from diagrams.generic.storage import Storage
from diagrams.onprem.compute import Server
from diagrams.onprem.queue import Nats
from diagrams.programming.language import Python

with Diagram(
    "Overall architecture",
    filename="images/overall",
    outformat="svg",
    show=False,
    direction="LR",
):
    python_client = Python("python_client")
    coordinator = Server("coordinator")

    with Cluster("nats_server (JetStream)"):
        jobs_kv = Nats("RAYTWIN_JOBS (KV)")
        tasks = Nats("RAYTWIN_TASKS")
        events = Nats("RAYTWIN_EVENTS")

    with Cluster("workers"):
        worker_cpu = Server("worker_cpu")
        worker_gpu = Server("worker_gpu")

    object_store = Storage("object_store\nmanifests, inputs, fields,\nparts, results")

    python_client >> Edge(label="submit, cancel") >> coordinator
    python_client >> Edge(label="watch state", style="dashed") >> jobs_kv
    coordinator >> Edge(label="write state") >> jobs_kv
    coordinator >> Edge(label="publish tasks", style="dashed") >> tasks
    tasks >> Edge(label="pull, batch 1", style="dashed") >> [worker_cpu, worker_gpu]
    [worker_cpu, worker_gpu] >> Edge(label="task done", style="dashed") >> events
    events >> Edge(label="consume", style="dashed") >> coordinator
    [worker_cpu, worker_gpu] >> Edge(label="read inputs, write parts") >> object_store
    coordinator >> Edge(label="merge parts, write result") >> object_store
    python_client >> Edge(label="write inputs, read result") >> object_store

# diagrams links each icon by an absolute local path. Embed the icons,
# so that the SVG renders on any machine and on GitHub.
svg_path = "images/overall.svg"
with open(svg_path, encoding="utf-8") as f:
    svg = f.read()
svg = re.sub(
    r'xlink:href="([^"]+\.png)"',
    lambda m: 'xlink:href="data:image/png;base64,'
    + base64.b64encode(open(m.group(1), "rb").read()).decode()
    + '"',
    svg,
)
with open(svg_path, "w", encoding="utf-8") as f:
    f.write(svg)
