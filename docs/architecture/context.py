# docs/architecture/context.py
import base64
import re

from diagrams import Cluster, Diagram, Edge
from diagrams.generic.storage import Storage
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.client import Users
from diagrams.onprem.compute import Server
from diagrams.onprem.queue import Nats

with Diagram(
    "System context",
    filename="images/context",
    outformat="svg",
    show=False,
    direction="LR",
):
    users = Users("researchers and\nSON applications")
    measurements = Storage("measurement data\nMDT, PM and CM\n(simulated in the MVP)")

    with Cluster("RayTwin"):
        system = Server("RayTwin")

    object_store = Storage("object store\nlocal disk, S3, MinIO")
    broker = Nats("NATS server\n(distributed mode)")
    ci = GithubActions("CI with the\nreference oracle")

    users >> Edge(label="manifests, jobs, results") >> system
    measurements >> Edge(label="calibration and scenario input") >> system
    system >> Edge(label="reads inputs, writes results") >> object_store
    system >> Edge(label="tasks, events, job state", style="dashed") >> broker
    ci >> Edge(label="compares each pull request") >> system

# diagrams links each icon by an absolute local path. Embed the icons,
# so that the SVG renders on any machine and on GitHub.
svg_path = "images/context.svg"
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
