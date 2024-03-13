import json
import os

from flask import Flask, jsonify, request

app = Flask(__name__)


def get_labels(name: str) -> dict:
    return {
        "demoapp.example.com/name": name,
    }


def get_service_account(name: str, labels: dict) -> dict:
    return {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {
            "name": name,
            "labels": labels,
        },
    }


def get_deployment(name: str, image: str, port: int, labels: dict, resources: dict = {}, replicas: int = 1) -> dict:
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name, "labels": labels},
        "spec": {
            "replicas": replicas,
            "selector": {"matchLabels": labels},
            "template": {
                "metadata": {"labels": labels},
                "spec": {
                    "containers": [
                        {
                            "name": name,
                            "image": image,
                            "ports": [{"containerPort": port, "name": "app"}],
                            "resources": resources,
                        }
                    ]
                },
            },
        },
    }


def get_service(name: str, port: int, labels: dict) -> dict:
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": name, "labels": labels},
        "spec": {
            "ports": [{"port": port, "targetPort": "app"}],
            "selector": labels,
        },
    }


@app.route("/sync", methods=["POST"])
def sync():

    app.logger.info("Received a sync request")

    hook_request = request.get_json()
    parent = hook_request.get("parent")
    children = hook_request.get("children")

    app.logger.info(f"Parent:\n {json.dumps(parent, indent=2)}")
    app.logger.info(f"Children:\n {json.dumps(children, indent=2)}")

    name = parent["metadata"]["name"]
    image = parent["spec"]["image"]
    port = parent["spec"]["port"]

    labels = get_labels(name)
    sa = get_service_account(name, labels)
    deployment = get_deployment(
        name,
        image,
        port,
        labels,
    )
    service = get_service(name, port, labels)

    return jsonify(
        {
            "status": {
                "deployments": len(children["Deployment.apps/v1"]),
                "services": len(children["Service.v1"]),
                "serviceaccounts": len(children["ServiceAccount.v1"]),
            },
            "children": [sa, deployment, service],
        }
    )


if __name__ == "__main__":
    loglevel = os.getenv("LOGLEVEL", "INFO")
    app.logger.setLevel(loglevel)
    app.run(host="0.0.0.0", port=5000, debug=True)
