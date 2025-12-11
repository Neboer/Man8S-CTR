from python_on_whales import docker, DockerClient

# # Specify nerdctl as the client
# nerdctl_client = DockerClient(client_call=["nerdctl"])

# # Now you can use nerdctl_client to interact with containerd via nerdctl commands
# nerdctl_client.pull("hello-world")
# nerdctl_client.run("hello-world")
# print(nerdctl_client.ps())

def compose_up(compose_file: str):
    """
    Bring up services defined in a Docker Compose file using nerdctl.
    """
    nerdctl_client = DockerClient(client_call=["nerdctl"])
    nerdctl_client.compose.up(compose_file, detach=True)
