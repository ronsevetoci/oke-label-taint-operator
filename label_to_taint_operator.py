# event_driven_label_to_taint_operator.py
# A Kopf-based Kubernetes operator that taints nodes based on their labels

import kopf
import kubernetes
import logging

# Node label and taint configuration
LABEL_KEY = "dedicated"
LABEL_VALUE = "ci"
TAINT_EFFECT = "NoSchedule"

@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    """
    Initialize logging and Kubernetes client configuration.
    """
    # Configure Python logging
    logging.basicConfig(level=logging.INFO)
    settings.posting.level = logging.INFO

    # Load in-cluster config so the operator can talk to the Kubernetes API
    kubernetes.config.load_incluster_config()

@kopf.on.event('', 'v1', 'nodes')
def on_node_event(event, **_):
    """
    Handle Node ADDED and MODIFIED events. Apply or remove taints based on node labels.
    """
    event_type = event.get('type')
    if event_type not in ('ADDED', 'MODIFIED'):
        return

    node_obj = event['object']
    node_name = node_obj.metadata.name
    labels = node_obj.metadata.labels or {}

    # Use a fresh read to get the latest taints
    v1 = kubernetes.client.CoreV1Api()
    node = v1.read_node(node_name)
    taints = node.spec.taints or []

    # Determine if we need to apply or remove the taint
    has_label = labels.get(LABEL_KEY) == LABEL_VALUE
    has_taint = any(
        t.key == LABEL_KEY and t.value == LABEL_VALUE and t.effect == TAINT_EFFECT
        for t in taints
    )

    if has_label and not has_taint:
        kopf.info(node, reason="Tainting", message=f"Tainting node {node_name}")
        # Append the new taint
        new_taints = taints + [
            kubernetes.client.V1Taint(
                key=LABEL_KEY,
                value=LABEL_VALUE,
                effect=TAINT_EFFECT
            )
        ]
        patch = {"spec": {"taints": [t.to_dict() for t in new_taints]}}
        v1.patch_node(node_name, patch)

    elif not has_label and has_taint:
        kopf.info(node, reason="RemovingTaint", message=f"Removing taint from node {node_name}")
        # Filter out the taint
        new_taints = [
            t for t in taints
            if not (t.key == LABEL_KEY and t.value == LABEL_VALUE and t.effect == TAINT_EFFECT)
        ]
        patch = {"spec": {"taints": [t.to_dict() for t in new_taints]}}
        v1.patch_node(node_name, patch)
