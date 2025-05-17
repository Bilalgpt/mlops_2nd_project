pipeline {
    agent any
    
    stages {
        stage('Checkout') {
            steps {
                // Clone the GitHub repository
                checkout scmGit(
                    branches: [[name: '*/main']], 
                    extensions: [], 
                    userRemoteConfigs: [[
                        credentialsId: 'github-token-2nd-project', 
                        url: 'https://github.com/Bilalgpt/mlops_2nd_project.git'
                    ]]
                )
                
                // Print confirmation message
                echo "Repository has been successfully cloned"
            }
        }
        
        stage('Create Virtual Environment') {
            steps {
                // Create and activate virtual environment
                sh '''
                # Remove any existing venv directory
                rm -rf venv || true
                
                # Create a new virtual environment
                python3 -m venv venv
                
                # Activate the virtual environment and install dependencies
                . venv/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
                
                echo "Virtual environment created and dependencies installed"
            }
        }
        
        stage('DVC Pull') {
            steps {
                // Use the GCP-KEY credential for DVC authentication
                withCredentials([file(credentialsId: 'GCP-KEY', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh '''
                    # Activate the virtual environment
                    . venv/bin/activate
                    
                    # Install DVC with Google Cloud support
                    pip install dvc dvc[gs]
                    
                    # Set the Google credentials and run DVC pull
                    export GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS
                    dvc pull
                    '''
                }
                
                echo "DVC pull completed successfully"
            }
        }
    }
    
    post {
        success {
            echo "Pipeline executed successfully!"
        }
        failure {
            echo "Pipeline execution failed!"
        }
        always {
            // Clean up virtual environment (optional - you can keep it for faster subsequent builds)
            sh 'rm -rf venv || true'
        }
    }
}
