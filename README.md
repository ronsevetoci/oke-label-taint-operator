# Label-to-Taint Operator

A Kubernetes operator built with [Kopf](https://kopf.readthedocs.io/en/stable/) that automatically taints nodes based on their labels. This is useful in environments like Oracle Kubernetes Engine (OKE), where managed node pools don’t natively support taints at creation, but you can label nodes via OCI CLI, Terraform, or the Console.

## 🚀 Features

- **Automatic Tainting**: Watches all `Node` objects and applies a taint when a node has the configured label.
- **Cleanup**: Removes the taint automatically if the label is removed.
- **Configurable**: Change the label key, label value, and taint effect in the operator code.
- **Lightweight**: Runs as a single Deployment with minimal RBAC.

## 📦 Repository Structure

```plaintext
├── Dockerfile
├── label_to_taint_operator.py  # Kopf operator logic
├── deploy.yaml                 # Combined Kubernetes manifests (Namespace, RBAC, Deployment)
└── README.md                   # This file
```

## 🔧 Prerequisites

- A running Kubernetes cluster (OKE or any conformant cluster).
- `kubectl` configured to access the cluster.
- Docker (or another OCI-compatible container registry).
- Python 3.11 (for local development).

## 🏗️ Installation

### 1. Build and Push Docker Image

```bash
# Replace <your-registry> with your Docker registry (Docker Hub, OCI Registry, etc.)
docker build -t <your-registry>/label-to-taint-operator:latest .
docker push <your-registry>/label-to-taint-operator:latest
```

### 2. Deploy Operator to Kubernetes

```bash
kubectl apply -f namespace.yaml
kubectl apply -f rbac.yaml
kubectl set image deployment/label-to-taint-operator \
  operator=<your-registry>/label-to-taint-operator:latest -n kopf-operator
kubectl apply -f deployment.yaml
```

## ⚙️ Configuration

Configuration is done by editing the constants at the top of `label_to_taint_operator.py`:

```python
# Key of the node label to watch
LABEL_KEY = "dedicated"
# Value of the node label to watch
LABEL_VALUE = "ci"
# Taint effect to apply (e.g., NoSchedule, NoExecute, PreferNoSchedule)
TAINT_EFFECT = "NoSchedule"
```

After making changes, rebuild and redeploy the image as shown above.

## 🎯 Usage

1. **Label a node** to trigger the taint:
   ```bash
   kubectl label nodes <node-name> dedicated=ci
   ```

2. **Verify the taint** is applied:
   ```bash
   kubectl get nodes -o custom-columns="NAME:.metadata.name,TAINTS:.spec.taints"
   ```

3. **Remove the label** to have the operator remove the taint:
   ```bash
   kubectl label nodes <node-name> dedicated-
   ```

4. **Verify** the taint is removed automatically.

## ⚠️ Scheduling Race Condition

When relying solely on the operator to taint nodes **after** they become available, there is a small window of time between:

1. **Node registration** (node becomes Ready in the API)  
2. **Scheduler evaluation** (pods may be scheduled immediately)  
3. **Operator reaction** (event-driven handler applies the taint)

During steps 1 → 2, pods without the appropriate tolerations **might** be scheduled onto a node that you intend to taint. To **eliminate this risk**, we recommend combining:

1. **Initial taint at kubelet registration** by passing the `--register-with-taints` flag via your custom `oke-init.sh` cloud-init script:

   ```bash
   bash /var/run/oke-init.sh \
     --kubelet-extra-args="--register-with-taints=dedicated=ci:NoSchedule"
   ```

   This ensures the node is tainted **before** it ever appears to the scheduler.

2. **Event-driven Kopf operator** (this repo) to keep taints in sync with labels (add/remove) dynamically.

3. (Optional) **Periodic reconciliation** with a timer as a fallback for self-healing.

By combining **registration-time taints** with an **event-driven operator**, you achieve **zero race** at node startup and **continuous** label-to-taint synchronization.

## 🛠️ Development & Testing

To run the operator locally (for debugging):

```bash
pip install kopf kubernetes
kopf run --standalone event_driven_label_to_taint_operator.py
```

Logs will be printed to your console.

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -m "Add YourFeature"`)
4. Push to your branch (`git push origin feature/YourFeature`)
5. Open a pull request

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
