FROM jenkins/jenkins:lts

USER root

RUN apt-get update -y && \
    apt-get install -y apt-transport-https ca-certificates curl gnupg software-properties-common && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    echo "deb [arch=amd64] https://download.docker.com/linux/debian bullseye stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update -y && \
    apt-get install -y docker-ce docker-ce-cli containerd.io && \
    apt-get clean

RUN apt-get update -y && \
    apt-get install -y python3 python3-pip python3-venv && \
    apt-get clean

RUN groupadd -f docker && \
    usermod -aG docker jenkins

RUN mkdir -p /var/lib/docker
VOLUME /var/lib/docker

RUN apt-get update -y && \
    apt-get install -y sudo && \
    echo "jenkins ALL=(ALL) NOPASSWD: /usr/bin/apt-get, /usr/bin/apt, /usr/bin/python3, /usr/bin/pip3" >> /etc/sudoers

USER jenkins
