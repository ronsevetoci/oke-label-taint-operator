import kopf
import kubernetes
import logging

# Configuration constants
LABEL_KEY = "dedicated"
LABEL_VALUE = "ci"
TAINT_EFFECT = "NoSchedule"

@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    # Set logging level
    settings.posting.level = logging.INFO

@kopf.timer('nodes', interval=30.0)
def auto_taint_nodes(**kwargs):
    # Initialize Kubernetes API client
    v1 = kubernetes.client.CoreV1Api()
    nodes = v1.list_node().items

    for node in nodes:
        labels = node.metadata.labels or {}
        taints = node.spec.taints or []
        node_name = node.metadata.name

        # If node has our label but no matching taint, apply it
        if labels.get(LABEL_KEY) == LABEL_VALUE:
            already = any(
                t.key == LABEL_KEY and t.value == LABEL_VALUE and t.effect == TAINT_EFFECT
                for t in taints
            )
            if not already:
                kopf.info(node, reason="Tainting", message=f"Tainting node {node_name}")
                taints.append(kubernetes.client.V1Taint(
                    key=LABEL_KEY,
                    value=LABEL_VALUE,
                    effect=TAINT_EFFECT
                ))
                patch = {"spec": {"taints": [t.to_dict() for t in taints]}}
                v1.patch_node(node_name, patch)
        else:
            # If label removed, optionally remove taint
            new = [t for t in taints if not (t.key == LABEL_KEY and t.value == LABEL_VALUE)]
            if len(new) != len(taints):
                kopf.info(node, reason="RemovingTaint", message=f"Removing taint from {node_name}")
                patch = {"spec": {"taints": [t.to_dict() for t in new]}}
                v1.patch_node(node_name, patch)