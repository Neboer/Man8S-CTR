# Man8S-CTR
Another container orchestration system. Man8S use yggdrasil as VPN networking, use containerd to maintain containers and images, and use a new kind of config manage various types of dirs of containers.

## The process for creating a container:
1. convert MBContainerConf to ComposeConf
2. create mount point source and change their owner/perm according to the config.
3. compose up the container.

## Limitation

in this version, we have these limitations:
- can't limit container's network connection.