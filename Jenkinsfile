pipeline {
    agent any
    
    environment {
        VENV_DIR = "${WORKSPACE}/venv"
        GOOGLE_APPLICATION_CREDENTIALS = credentials('GCP-KEY')
        PROJECT_ID = "mlops-459315"
        IMAGE_NAME = "ml-recommendation-app"
        IMAGE_TAG = "${BUILD_NUMBER}"
        GCR_URL = "gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}"
        CLUSTER_NAME = "ml-ops-2nd-project-cluster-1" // Your actual cluster name
        CLUSTER_REGION = "us-central1" // Your cluster is regional, not zonal
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scmGit(
                    branches: [[name: '*/main']], 
                    extensions: [], 
                    userRemoteConfigs: [[
                        credentialsId: 'ml-ops-2nd-project', 
                        url: 'https://github.com/Bilalgpt/mlops_2nd_project.git'
                    ]]
                )
                echo "Repository has been successfully cloned"
            }
        }
        
        stage('Setup Virtual Environment') {
            steps {
                sh '''
                echo "===== Creating Virtual Environment ====="
                python3 -m venv ${VENV_DIR} || python -m venv ${VENV_DIR}
                echo "Virtual environment created successfully"
                '''
            }
        }
        
        stage('Install Dependencies') {
            steps {
                sh '''
                echo "===== Installing Dependencies ====="
                # Activate virtual environment
                . ${VENV_DIR}/bin/activate
                
                # Upgrade pip
                pip install --upgrade pip
                
                # Install project in development mode (using setup.py)
                pip install -e .
                
                # List installed packages for verification
                pip list
                '''
            }
        }
        
        stage('DVC Pull') {
            steps {
                sh '''
                echo "===== Pulling data with DVC ====="
                # Activate virtual environment
                . ${VENV_DIR}/bin/activate
                
                # Configure GCP authentication
                echo "Setting up GCP authentication"
                
                # Initialize DVC if needed
                dvc status || dvc init
                
                # Pull data from remote storage
                echo "Pulling data artifacts from remote storage"
                dvc pull -v
                
                # Show DVC status for verification
                dvc status
                '''
            }
        }
        
        stage('Authenticate with GCP') {
            steps {
                sh '''
                echo "===== Authenticating with Google Cloud ====="
                # Use the service account key for authentication
                gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                
                # Configure Docker to use gcloud as a credential helper
                gcloud auth configure-docker gcr.io -q
                
                # Verify authentication
                gcloud config list
                '''
            }
        }
        
        stage('Fix Docker Permissions') {
            steps {
                sh '''
                echo "===== Fixing Docker Socket Permissions ====="
                # This will ensure the Docker socket is readable by the jenkins user
                # Note: This requires that the Jenkins container is run with privileged mode
                ls -la /var/run/docker.sock || echo "Docker socket not found at expected location"
                
                # Try running a basic Docker command to check if permissions are already correct
                docker version || (echo "Attempting to fix Docker socket permissions" && \
                    (chown root:root /var/run/docker.sock || echo "Failed to change ownership") && \
                    (chmod 666 /var/run/docker.sock || echo "Failed to change permissions"))
                '''
            }
        }
        
        stage('Build Docker Image') {
            steps {
                sh '''
                echo "===== Building Docker Image ====="
                # Build the Docker image (without sudo)
                docker build -t ${GCR_URL} .
                
                # List images to verify build
                docker images | grep ${IMAGE_NAME}
                '''
            }
        }
        
        stage('Push to GCR') {
            steps {
                sh '''
                echo "===== Pushing Image to Google Container Registry ====="
                # Push the Docker image to GCR (without sudo)
                docker push ${GCR_URL}
                
                echo "Image successfully pushed to: ${GCR_URL}"
                '''
            }
        }
        
        stage('Deploy to Kubernetes') {
            steps {
                sh '''
                echo "===== Deploying to Kubernetes ====="
                # Install kubectl if needed
                if ! command -v kubectl &> /dev/null; then
                    echo "Installing kubectl..."
                    curl -LO "https://dl.k8s.io/release/stable.txt"
                    curl -LO "https://dl.k8s.io/$(cat stable.txt)/bin/linux/amd64/kubectl"
                    chmod +x kubectl
                    mv kubectl /usr/local/bin/
                fi
                
                # Get GKE cluster credentials - note we use --region not --zone for regional clusters
                gcloud container clusters get-credentials ${CLUSTER_NAME} --region ${CLUSTER_REGION} --project ${PROJECT_ID}
                
                # Create or update deployment.yml file with current image tag
                cat <<EOF > deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-recommendation-app
  labels:
    app: ml-recommendation-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ml-recommendation-app
  template:
    metadata:
      labels:
        app: ml-recommendation-app
    spec:
      containers:
      - name: ml-recommendation-app
        image: ${GCR_URL}
        imagePullPolicy: Always
        ports:
        - containerPort: 5000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
        livenessProbe:
          httpGet:
            path: /
            port: 5000
          initialDelaySeconds: 60
          periodSeconds: 20
          timeoutSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ml-recommendation-service
  labels:
    app: ml-recommendation-app
spec:
  type: LoadBalancer
  selector:
    app: ml-recommendation-app
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
EOF
                
                # Apply the Kubernetes configuration
                kubectl apply -f deployment.yml
                
                # Wait for deployment to complete
                kubectl rollout status deployment/ml-recommendation-app --timeout=300s
                
                # Get service details and external IP
                echo "===== Service Details ====="
                kubectl get service ml-recommendation-service
                
                # Wait for external IP (may take a minute or two)
                echo "Waiting for external IP..."
                for i in {1..10}; do
                    EXTERNAL_IP=$(kubectl get service ml-recommendation-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
                    if [ -n "$EXTERNAL_IP" ]; then
                        echo "Application is deployed and available at: http://$EXTERNAL_IP"
                        break
                    fi
                    echo "Waiting for external IP assignment... ($i/10)"
                    sleep 30
                done
                '''
            }
        }
    }
    
    post {
        success {
            echo "Pipeline completed successfully!"
            echo "Docker image pushed to: ${GCR_URL}"
            echo "Application deployed to Kubernetes Autopilot cluster: ${CLUSTER_NAME}"
        }
        failure {
            echo "Pipeline failed. Please check the logs."
        }
        always {
            echo "Pipeline execution completed."
            
            // Clean up Docker images to save space
            sh '''
            echo "Cleaning up Docker images..."
            docker rmi ${GCR_URL} || true
            '''
        }
    }
}
