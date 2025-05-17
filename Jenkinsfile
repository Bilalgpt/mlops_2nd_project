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
                sh '''
                python -m pip install --upgrade pip
                python -m pip install virtualenv
                python -m virtualenv venv
                '''
                
                // Activate virtual environment and install requirements
                sh '''
                . venv/bin/activate
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
                    . venv/bin/activate
                    pip install dvc dvc[gs]
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
            // Clean up virtual environment
            sh 'rm -rf venv'
        }
    }
}
