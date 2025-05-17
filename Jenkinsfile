pipeline {
    agent any
    
    environment {
        VENV_DIR = "${WORKSPACE}/venv"
        GOOGLE_APPLICATION_CREDENTIALS = credentials('GCP-KEY')
        PROJECT_ID = "mlops-2nd-project"
        IMAGE_NAME = "ml-recommendation-app"
        IMAGE_TAG = "${BUILD_NUMBER}"
        GCR_URL = "gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}"
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
    }
    
    post {
        success {
            echo "Pipeline completed successfully!"
            echo "Docker image pushed to: ${GCR_URL}"
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
