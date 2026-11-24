provider "kubernetes" {
  config_path = pathexpand(var.kubeconfig_path)
}

resource "kubernetes_namespace_v1" "platform" {
  metadata {
    name = "ai-platform"
    labels = {"app.kubernetes.io/part-of" = "ai-infrastructure-platform"}
  }
}

resource "kubernetes_config_map_v1" "config" {
  metadata {
    name = "inference-config"
    namespace = kubernetes_namespace_v1.platform.metadata[0].name
  }
  data = {
    REDIS_URL = "redis://redis:6379/0"
    REDIS_STREAM = "inference:jobs"
    REDIS_GROUP = "inference-workers"
    MAX_RETRIES = "3"
  }
}

resource "kubernetes_secret_v1" "secret" {
  metadata {
    name = "inference-secret"
    namespace = kubernetes_namespace_v1.platform.metadata[0].name
  }
  type = "Opaque"
  data = {DEMO_SECRET = "replace-this-local-demo-value"}
}

resource "kubernetes_deployment_v1" "redis" {
  metadata {
    name = "redis"
    namespace = kubernetes_namespace_v1.platform.metadata[0].name
    labels = {app = "redis"}
  }
  spec {
    replicas = 1
    selector {
      match_labels = {app = "redis"}
    }
    template {
      metadata {
        labels = {app = "redis"}
      }
      spec {
        container {
          name = "redis"
          image = "redis:7.4-alpine"
          args = ["redis-server", "--appendonly", "yes"]
          port {
            container_port = 6379
          }
          resources {
            requests = {cpu = "50m", memory = "64Mi"}
            limits = {cpu = "500m", memory = "256Mi"}
          }
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "redis" {
  metadata {
    name = "redis"
    namespace = kubernetes_namespace_v1.platform.metadata[0].name
  }
  spec {
    selector = {app = "redis"}
    port {
      port = 6379
      target_port = 6379
    }
  }
}

resource "kubernetes_deployment_v1" "api" {
  metadata {
    name = "inference-api"
    namespace = kubernetes_namespace_v1.platform.metadata[0].name
    labels = {app = "inference-api"}
  }
  spec {
    replicas = 2
    selector {
      match_labels = {app = "inference-api"}
    }
    template {
      metadata {
        labels = {app = "inference-api"}
      }
      spec {
        security_context {
          run_as_non_root = true
          run_as_user = 10001
          run_as_group = 10001
        }
        container {
          name = "api"
          image = var.image
          image_pull_policy = "IfNotPresent"
          command = ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
          port {
            container_port = 8000
          }
          env_from {
            config_map_ref {
              name = kubernetes_config_map_v1.config.metadata[0].name
            }
          }
          env {
            name = "DEMO_SECRET"
            value_from {
              secret_key_ref {
                name = kubernetes_secret_v1.secret.metadata[0].name
                key = "DEMO_SECRET"
              }
            }
          }
          readiness_probe {
            http_get {
              path = "/ready"
              port = 8000
            }
            initial_delay_seconds = 5
            period_seconds = 5
          }
          liveness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 10
            period_seconds = 10
          }
          resources {
            requests = {cpu = "100m", memory = "128Mi"}
            limits = {cpu = "1", memory = "512Mi"}
          }
        }
      }
    }
  }
  depends_on = [kubernetes_deployment_v1.redis]
}

resource "kubernetes_service_v1" "api" {
  metadata {
    name = "inference-api"
    namespace = kubernetes_namespace_v1.platform.metadata[0].name
  }
  spec {
    selector = {app = "inference-api"}
    port {
      port = 8000
      target_port = 8000
    }
  }
}

resource "kubernetes_deployment_v1" "worker" {
  metadata {
    name = "inference-worker"
    namespace = kubernetes_namespace_v1.platform.metadata[0].name
    labels = {app = "inference-worker"}
  }
  spec {
    replicas = 2
    selector {
      match_labels = {app = "inference-worker"}
    }
    template {
      metadata {
        labels = {app = "inference-worker"}
      }
      spec {
        security_context {
          run_as_non_root = true
          run_as_user = 10001
          run_as_group = 10001
        }
        container {
          name = "worker"
          image = var.image
          image_pull_policy = "IfNotPresent"
          command = ["python", "-m", "app.worker"]
          env_from {
            config_map_ref {
              name = kubernetes_config_map_v1.config.metadata[0].name
            }
          }
          env {
            name = "REDIS_CONSUMER"
            value_from {
              field_ref {
                field_path = "metadata.name"
              }
            }
          }
          resources {
            requests = {cpu = "100m", memory = "128Mi"}
            limits = {cpu = "1", memory = "512Mi"}
          }
        }
      }
    }
  }
  depends_on = [kubernetes_deployment_v1.redis]
}

resource "kubernetes_horizontal_pod_autoscaler_v2" "api" {
  metadata {
    name = "inference-api"
    namespace = kubernetes_namespace_v1.platform.metadata[0].name
  }
  spec {
    min_replicas = 2
    max_replicas = 6
    scale_target_ref {
      api_version = "apps/v1"
      kind = "Deployment"
      name = kubernetes_deployment_v1.api.metadata[0].name
    }
    metric {
      type = "Resource"
      resource {
        name = "cpu"
        target {
          type = "Utilization"
          average_utilization = 70
        }
      }
    }
  }
}

resource "kubernetes_horizontal_pod_autoscaler_v2" "worker" {
  metadata {
    name = "inference-worker"
    namespace = kubernetes_namespace_v1.platform.metadata[0].name
  }
  spec {
    min_replicas = 2
    max_replicas = 8
    scale_target_ref {
      api_version = "apps/v1"
      kind = "Deployment"
      name = kubernetes_deployment_v1.worker.metadata[0].name
    }
    metric {
      type = "Resource"
      resource {
        name = "cpu"
        target {
          type = "Utilization"
          average_utilization = 70
        }
      }
    }
  }
}

output "namespace" {
  value = kubernetes_namespace_v1.platform.metadata[0].name
}
output "api_service" {
  value = "inference-api.ai-platform.svc.cluster.local:8000"
}
