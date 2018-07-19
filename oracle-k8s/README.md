# Getting OKE K8s working...

Followed the tutorial [here](http://www.oracle.com/webfolder/technetwork/tutorials/obe/oci/oke-full/index.html)
to create the k8s cluster that I have called "bss-cluster"

# Connecting to the cluster

Now that the cluster has been created I used the `get-kubeconfig.sh` script
to get the `kubeconfig` file that allows me to connect. I can connect
to the cluster using

```
$ export KUBECONFIG=./kubeconfig
$ kubectl get nodes
NAME            STATUS    ROLES     AGE       VERSION
130.61.26.49    Ready     node      13d       v1.9.7
130.61.43.213   Ready     node      13d       v1.9.7
130.61.91.160   Ready     node      13d       v1.9.7
```

I can then connect to the Kubernetes dashboard by typing

```
$ kubectl proxy
```

and then connecting to `http://127.0.0.1:8001/ui` in my browser.

## Helm and jupyterhub

I now tried to install JupyterHub using helm

```
$ helm init
$HELM_HOME has been configured at /home/chris/.helm.
Warning: Tiller is already installed in the cluster.
(Use --client-only to suppress this message, or --upgrade to upgrade Tiller to the current version.)
Happy Helming!
```

Now need to update the repo so we can download jupyterhub

```
$ helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
$ help repo update
```

I have copied the `notebook.yaml` file from the biosimspace notebook
and told it to use the `chryswoods/cryoschool:v1` image that I created
for the Cryo-EM schools event.

Now I will install this using

```
$ helm install jupyterhub/jupyterhub --version=v0.6 --timeout=36000 --debug --name=notebook --namespace=notebook -f notebook.yaml
```

