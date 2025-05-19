pipeline {
    agent any
    
    environment {
        PROJECT_ID = 'mlops-459315'
        CLUSTER_NAME = 'mlops2ndproject'
        CLUSTER_ZONE = 'us-central1'
        IMAGE_NAME = 'ml-recommendation-app'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        IMAGE_URL = "gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}"
        CREDENTIALS_ID = 'GCP-KEY'  // Updated to match your Jenkins credential ID
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo "===> DEBUG: Repository checkout complete"
            }
        }
        
        stage('Build and Push Docker Image') {
            steps {
                script {
                    // Authenticate with Google Cloud using correct credential ID
                    withCredentials([file(credentialsId: "${CREDENTIALS_ID}", variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                        sh '''
                        echo "===> DEBUG: Authenticating with Google Cloud"
                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                        gcloud config set project ${PROJECT_ID}
                        gcloud auth configure-docker
                        
                        echo "===> DEBUG: Starting Docker build with memory monitoring"
                        # Print system resources before build
                        echo "===> SYSTEM RESOURCES BEFORE BUILD:"
                        free -h || echo "free command not available"
                        df -h
                        
                        # Build with progress output
                        echo "===> DEBUG: Building Docker image ${IMAGE_URL}"
                        docker build -t ${IMAGE_URL} .
                        
                        # Check image size
                        echo "===> DEBUG: Image size information:"
                        docker images ${IMAGE_URL} --format "{{.Size}}"
                        
                        # Print system resources after build
                        echo "===> SYSTEM RESOURCES AFTER BUILD:"
                        free -h || echo "free command not available"
                        df -h
                        
                        echo "===> DEBUG: Pushing Docker image to registry"
                        docker push ${IMAGE_URL}
                        echo "===> DEBUG: Image push complete"
                        '''
                    }
                }
            }
        }
        
        stage('Deploy to GKE') {
            steps {
                script {
                    withCredentials([file(credentialsId: "${CREDENTIALS_ID}", variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                        sh '''
                        echo "===> DEBUG: Connecting to GKE cluster ${CLUSTER_NAME}"
                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                        gcloud container clusters get-credentials ${CLUSTER_NAME} --zone ${CLUSTER_ZONE} --project ${PROJECT_ID}
                        
                        # Check cluster node capacity
                        echo "===> DEBUG: Cluster node details and capacity:"
                        kubectl describe nodes | grep -A 5 "Capacity\\|Allocatable" || echo "No node information available"
                        '''
                        
                        // Create the deployment YAML with proper resource limits
                        sh '''
                        echo "===> DEBUG: Creating deployment manifest with 2Gi memory limit"
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
        image: ${IMAGE_URL}
        ports:
        - containerPort: 5000
        resources:
          limits:
            cpu: 1000m
            memory: 2Gi
          requests:
            cpu: 500m
            memory: 1Gi
        env:
        - name: GOOGLE_APPLICATION_CREDENTIALS
          value: /var/secrets/google/key.json
        - name: DEBUG_MODE
          value: "true"
        volumeMounts:
        - name: gcp-key
          mountPath: /var/secrets/google
          readOnly: true
      volumes:
      - name: gcp-key
        secret:
          secretName: gcp-key
EOF

                        # Create or update the service
                        echo "===> DEBUG: Creating service manifest"
                        cat <<EOF > service.yaml
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
                        '''
                        
                        // Check if secret exists and create if it doesn't
                        sh '''
                        echo "===> DEBUG: Setting up GCP credentials secret"
                        if ! kubectl get secret gcp-key &>/dev/null; then
                          kubectl create secret generic gcp-key --from-file=key.json=${GOOGLE_APPLICATION_CREDENTIALS}
                          echo "===> DEBUG: Created new GCP credentials secret"
                        else
                          echo "===> DEBUG: GCP credentials secret already exists"
                          # Update the secret with the current key
                          kubectl create secret generic gcp-key --from-file=key.json=${GOOGLE_APPLICATION_CREDENTIALS} --dry-run=client -o yaml | kubectl apply -f -
                          echo "===> DEBUG: Updated GCP credentials secret"
                        fi
                        '''
                        
                        // Apply the deployment and service
                        sh '''
                        echo "===> DEBUG: Applying deployment to cluster"
                        kubectl apply -f deployment.yaml
                        kubectl apply -f service.yaml
                        
                        echo "===> DEBUG: Deployment applied, waiting for rollout"
                        '''
                        
                        // Wait for deployment to complete and monitor resources
                        sh '''
                        # Monitor the deployment rollout
                        kubectl rollout status deployment/ml-recommendation-app --timeout=5m
                        
                        echo "===> DEBUG: Deployment completed, checking pod status"
                        kubectl get pods -l app=ml-recommendation-app
                        
                        echo "===> DEBUG: Checking resource allocation for pods"
                        kubectl describe pods -l app=ml-recommendation-app | grep -A 3 "Limits\\|Requests" || echo "No resource limits found"
                        
                        # Wait for pods to be ready
                        sleep 30
                        
                        echo "===> DEBUG: Monitoring memory usage of pods"
                        kubectl top pods -l app=ml-recommendation-app || echo "kubectl top not available"
                        
                        echo "===> DEBUG: Checking recent pod logs for memory indicators"
                        for pod in $(kubectl get pods -l app=ml-recommendation-app -o name); do
                          echo "===> LOGS FOR $pod:"
                          kubectl logs $pod --tail=50 | grep -i "memory\\|heap\\|OOM" || echo "No memory-related logs found"
                        done
                        
                        # Get the service URL
                        echo "===> APPLICATION ENDPOINT:"
                        echo "http://$(kubectl get service ml-recommendation-app -o jsonpath='{.status.loadBalancer.ingress[0].ip}')"
                        '''
                        
                        // Generate resource usage report
                        sh '''
                        echo "===> RESOURCE USAGE SUMMARY:"
                        echo "Pods running with following resource allocations:"
                        kubectl get pods -l app=ml-recommendation-app -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,RESTARTS:.status.containerStatuses[0].restartCount
                        kubectl top pods -l app=ml-recommendation-app || echo "kubectl top not available"
                        
                        echo "===> DEPLOYMENT SUCCESSFUL: ML Recommendation app is now running"
                        '''
                    }
                }
            }
        }
        
        stage('Verify Application Health') {
            steps {
                script {
                    withCredentials([file(credentialsId: "${CREDENTIALS_ID}", variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                        sh '''
                        echo "===> DEBUG: Verifying application health"
                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                        gcloud container clusters get-credentials ${CLUSTER_NAME} --zone ${CLUSTER_ZONE} --project ${PROJECT_ID}
                        
                        # Wait for service to get external IP
                        external_ip=""
                        count=0
                        while [ -z "$external_ip" ] && [ $count -lt 10 ]; do
                          echo "===> DEBUG: Waiting for external IP... Attempt $count"
                          external_ip=$(kubectl get service ml-recommendation-app -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
                          [ -z "$external_ip" ] && sleep 10
                          count=$((count+1))
                        done
                        
                        if [ -z "$external_ip" ]; then
                          echo "===> WARNING: No external IP found after timeout"
                        else
                          echo "===> DEBUG: Service endpoint available at: http://$external_ip"
                        fi
                        
                        # Monitor initial resource usage after deployment
                        echo "===> DEBUG: Resource usage after deployment:"
                        kubectl top pods -l app=ml-recommendation-app || echo "kubectl top not available"
                        
                        # Check for any restarts which could indicate OOM issues
                        echo "===> DEBUG: Checking for container restarts (potential OOM indicators):"
                        kubectl get pods -l app=ml-recommendation-app -o custom-columns=NAME:.metadata.name,RESTARTS:.status.containerStatuses[0].restartCount
                        
                        echo "===> VERIFICATION COMPLETE: Application is deployed and running"
                        '''
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo "===> DEBUG: Pipeline completed successfully"
        }
        failure {
            echo "===> DEBUG: Pipeline failed, check logs for details"
        }
        always {
            echo "===> DEBUG: Cleaning workspace"
            // Use deleteDir() instead of cleanWs()
            deleteDir()
        }
    }
}
