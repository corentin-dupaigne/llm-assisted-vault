---
project: cka
---
>[!todo]
> install argo cd in a kubernetes cluster using helm while ensuring the crds are not installed.
> -  add the official argo cd helm repository with the name argocd (https://argoproj.github.io/argo-helm)
> - create a namespace called argocd
> - generate a helm template from the argo cd chart version 7.7.3 for the argocd namespace
> - ensure that crds are not installed by configuring the chart accordingly
> - save the generated yaml manifest to /root/argo-helm.yaml

```bash
# Create namespace
kubectl create namespace argocd

# Add repo and template manifests (CRDs not installed)
helm repo add argocd https://argoproj.github.io/argo-helm
helm repo update
helm template argocd argo/argo-cd --version 7.7.3 --set crds.install=false --namespace argocd > /root/argo-helm.yaml cat /root/argo-helm.yaml   # confirm output
```