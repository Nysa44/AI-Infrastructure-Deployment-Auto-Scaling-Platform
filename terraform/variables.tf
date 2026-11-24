variable "kubeconfig_path" {
  description = "Kubeconfig path for an existing Kubernetes cluster."
  type = string
  default = "~/.kube/config"
}
variable "image" {
  description = "Image already loaded/pulled by the cluster."
  type = string
  default = "ai-inference-platform:1.0.0"
}
