FROM jenkins/jenkins:lts

USER root

# Install Docker CLI
RUN apt-get update -y && \
    apt-get install -y apt-transport-https ca-certificates curl gnupg software-properties-common && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    echo "deb [arch=amd64] https://download.docker.com/linux/debian bullseye stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update -y && \
    apt-get install -y docker-ce-cli && \
    apt-get clean

# Install Google Cloud SDK and Kubernetes tools
RUN apt-get update -y && \
    apt-get install -y apt-transport-https ca-certificates gnupg curl && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update -y && \
    apt-get install -y google-cloud-sdk google-cloud-sdk-gke-gcloud-auth-plugin kubectl && \
    apt-get clean

# Install Python and development tools
RUN apt-get update -y && \
    apt-get install -y python3 python3-pip python3-venv python3-full && \
    apt-get clean

# Create and use a virtual environment for Python packages
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python packages in the virtual environment
RUN pip install --upgrade pip setuptools wheel && \
    pip install dvc "dvc[gs]"

# Configure Docker group and permissions
RUN groupadd -f docker && \
    usermod -aG docker jenkins

# Configure sudo access
RUN apt-get update -y && \
    apt-get install -y sudo && \
    echo "jenkins ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    apt-get clean

# Create necessary directories with proper permissions
RUN mkdir -p /var/jenkins_home/.kube /var/jenkins_home/.config /var/jenkins_home/.cache/pip && \
    chown -R jenkins:jenkins /var/jenkins_home/.kube /var/jenkins_home/.config /var/jenkins_home/.cache

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy plugins list and install Jenkins plugins
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

USER jenkins

ENTRYPOINT ["/entrypoint.sh"]
