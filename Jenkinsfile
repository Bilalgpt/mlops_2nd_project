pipeline {
    agent any
    
    environment {
        VENV_DIR = "${WORKSPACE}/venv"
        GOOGLE_APPLICATION_CREDENTIALS = credentials('GCP-KEY')
        PROJECT_ID = "mlops-459315"
        IMAGE_NAME = "ml-recommendation-app"
        IMAGE_TAG = "${BUILD_NUMBER}"
        GCR_URL = "gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}"
        CLUSTER_NAME = "ml-ops-2nd-project-cluster-1"
        CLUSTER_REGION = "us-central1"
        PATH = "${env.WORKSPACE}/bin:${env.PATH}"
        USE_GKE_GCLOUD_AUTH_PLUGIN = "True"
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
        
        stage('Build Docker Image') {
            steps {
                sh '''
                echo "===== Building Docker Image ====="
                # Build the Docker image
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
                # Push the Docker image to GCR
                docker push ${GCR_URL}
                
                echo "Image successfully pushed to: ${GCR_URL}"
                '''
            }
        }
        
        stage('Deploy to Kubernetes') {
            steps {
                sh '''
                echo "===== Deploying to Kubernetes ====="
                # Create local bin directory if needed for kubectl
                mkdir -p ${WORKSPACE}/bin
                
                # Install kubectl if needed
                if ! command -v kubectl &> /dev/null; then
                    echo "Installing kubectl..."
                    curl -LO "https://dl.k8s.io/release/stable.txt"
                    curl -LO "https://dl.k8s.io/$(cat stable.txt)/bin/linux/amd64/kubectl"
                    chmod +x kubectl
                    mv kubectl ${WORKSPACE}/bin/
                    export PATH=${WORKSPACE}/bin:$PATH
                fi
                
                # Set environment variables for kubectl
                export USE_GKE_GCLOUD_AUTH_PLUGIN=True
                
                # Verify gke-gcloud-auth-plugin is available
                echo "Verifying GKE auth plugin installation:"
                which gke-gcloud-auth-plugin || echo "GKE auth plugin not found in PATH"
                
                # Get GKE cluster credentials
                gcloud container clusters get-credentials ${CLUSTER_NAME} --region ${CLUSTER_REGION} --project ${PROJECT_ID}
                
                # Update the image in deployment.yaml with new tag
                echo "Updating deployment.yaml with new image: ${GCR_URL}"
                sed -i "s|gcr.io/${PROJECT_ID}/${IMAGE_NAME}:[0-9]*|${GCR_URL}|g" deployment.yaml
                
                # Show the updated deployment file
                echo "Updated deployment configuration:"
                cat deployment.yaml
                
                # Apply the deployment
                kubectl apply -f deployment.yaml
                
                # Wait for deployment to roll out
                kubectl rollout status deployment/ml-recommendation-app --timeout=300s
                
                # Get service information
                echo "===== Service Details ====="
                kubectl get service ml-recommendation-service
                
                # Wait for external IP
                echo "Waiting for external IP..."
                for i in {1..5}; do
                    EXTERNAL_IP=$(kubectl get service ml-recommendation-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
                    if [ -n "$EXTERNAL_IP" ]; then
                        echo "Application is deployed and available at: http://$EXTERNAL_IP"
                        break
                    fi
                    echo "Waiting for external IP assignment... ($i/5)"
                    sleep 20
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
