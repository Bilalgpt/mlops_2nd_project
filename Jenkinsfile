pipeline {
    agent any
    
    environment {
        PROJECT_ID = 'mlops-459315'
        CLUSTER_NAME = 'ml-ops-2nd-project-cluster-12'
        LOCATION = 'us-central1'
        CREDENTIALS_ID = 'GCP-KEY'
        GIT_CREDENTIALS_ID = 'git-token'
        IMAGE_NAME = 'ml-recommendation-app'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        VENV_NAME = 'venv'
    }
    
    stages {
        stage('Cloning from Github....') {
            steps {
                checkout([$class: 'GitSCM', 
                    branches: [[name: '*/main']], 
                    extensions: [], 
                    userRemoteConfigs: [[
                        credentialsId: "${GIT_CREDENTIALS_ID}",
                        url: 'https://github.com/Bilalgpt/mlops_2nd_project.git'
                    ]]
                ])
                echo "Successfully cloned the repository."
            }
        }
        
        stage('Making a virtual environment....') {
            steps {
                sh '''
                python -m venv ${VENV_NAME}
                . ${VENV_NAME}/bin/activate
                pip install --upgrade pip
                pip install -e .
                pip list
                '''
                echo "Virtual environment created and dependencies installed."
            }
        }
        
        stage('DVC Pull') {
            steps {
                withCredentials([file(credentialsId: "${CREDENTIALS_ID}", variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh '''
                    . ${VENV_NAME}/bin/activate
                    export GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS
                    dvc pull
                    '''
                }
                echo "DVC pull completed successfully."
            }
        }
        
        stage('Build and Push Image to GCR') {
            steps {
                withCredentials([file(credentialsId: "${CREDENTIALS_ID}", variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh '''
                    gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
                    gcloud config set project ${PROJECT_ID}
                    
                    # Build the Docker image
                    docker build -t gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG} .
                    
                    # Configure Docker to use gcloud as a credential helper
                    gcloud auth configure-docker -q
                    
                    # Push the image to Container Registry
                    docker push gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}
                    
                    # Tag as latest too
                    docker tag gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG} gcr.io/${PROJECT_ID}/${IMAGE_NAME}:latest
                    docker push gcr.io/${PROJECT_ID}/${IMAGE_NAME}:latest
                    '''
                }
                echo "Docker image built and pushed to GCR successfully."
            }
        }
        
        stage('Deploying to Kubernetes') {
            steps {
                withCredentials([file(credentialsId: "${CREDENTIALS_ID}", variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh '''
                    gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
                    gcloud config set project ${PROJECT_ID}
                    gcloud container clusters get-credentials ${CLUSTER_NAME} --region ${LOCATION} --project ${PROJECT_ID}
                    
                    # Create deployment manifest
                    cat <<EOF > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-recommendation-app
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
        image: gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}
        ports:
        - containerPort: 5000
        resources:
          limits:
            cpu: 500m
            memory: 512Mi
          requests:
            cpu: 200m
            memory: 256Mi
---
apiVersion: v1
kind: Service
metadata:
  name: ml-recommendation-app
spec:
  selector:
    app: ml-recommendation-app
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer
EOF

                    # Try deploying with retries
                    MAX_ATTEMPTS=5
                    for i in $(seq 1 $MAX_ATTEMPTS); do
                      kubectl apply -f deployment.yaml && break
                      echo "Attempt $i failed, retrying in 10 seconds..."
                      sleep 10
                      [ $i -eq $MAX_ATTEMPTS ] && echo "Failed to deploy after $MAX_ATTEMPTS attempts" && exit 1
                    done
                    
                    # Display service information
                    kubectl get service ml-recommendation-app
                    '''
                }
                echo "Deployed to Kubernetes successfully."
            }
        }
    }
    
    post {
        success {
            echo "Pipeline executed successfully!"
        }
        failure {
            echo "Pipeline execution failed. Please check the logs for details."
        }
        always {
            echo "Cleaning up workspace..."
            deleteDir()
        }
    }
}
