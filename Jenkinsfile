pipeline {
    agent any
    
    environment {
        VENV_DIR = "${WORKSPACE}/venv"
        GOOGLE_APPLICATION_CREDENTIALS = credentials('GCP-KEY')
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
    }
    
    post {
        success {
            echo "Pipeline completed successfully!"
        }
        failure {
            echo "Pipeline failed. Please check the logs."
        }
        always {
            echo "Pipeline execution completed."
        }
    }
}
