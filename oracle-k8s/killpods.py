
import os

pods = os.popen("kubectl --namespace notebook get pods", "r").readlines()

for pod in pods:
    if pod.find("Evicted") != -1:
        pod = pod.split()[0]
        print(pod)
        os.system("kubectl --namespace notebook delete pod %s" % pod)


