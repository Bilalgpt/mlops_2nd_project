pipeline {
    agent any
    
    environment {
        VENV_DIR = "${WORKSPACE}/venv"
    }
    
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
        
        stage('Debug Environment') {
            steps {
                sh '''
                echo "===== System Information ====="
                uname -a
                
                echo "\\n===== Python Version ====="
                python3 --version
                which python3
                
                echo "\\n===== Pip Version ====="
                pip3 --version
                which pip3
                
                echo "\\n===== Available Python Packages ====="
                pip3 list
                
                echo "\\n===== Directory Structure ====="
                ls -la
                
                echo "\\n===== setup.py Content ====="
                cat setup.py || echo "setup.py not found"
                
                echo "\\n===== requirements.txt Content ====="
                cat requirements.txt || echo "requirements.txt not found"
                '''
            }
        }
        
        stage("Making a virtual environment....") {
            steps {
                script {
                    echo 'Making a virtual environment...'
                    sh '''
                    # First, make sure python3-venv is installed
                    apt-get update && apt-get install -y python3-venv || echo "Could not install python3-venv, trying to continue anyway"
                    
                    # Remove any existing venv
                    rm -rf ${VENV_DIR} || true
                    
                    # Create virtual environment
                    python3 -m venv ${VENV_DIR} || python -m venv ${VENV_DIR}
                    
                    # Activate and install dependencies
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -e .
                    pip install dvc dvc[gs]
                    '''
                }
            }
        }
        
        stage('DVC Pull') {
            steps {
                // Use the GCP-KEY credential for DVC authentication
                withCredentials([file(credentialsId: 'GCP-KEY', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh '''
                    echo "===== Running DVC Pull ====="
                    # Activate the virtual environment
                    . ${VENV_DIR}/bin/activate
                    
                    # Set the Google credentials
                    export GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS
                    echo "Credentials file exists: $(test -f $GOOGLE_APPLICATION_CREDENTIALS && echo 'Yes' || echo 'No')"
                    
                    # Debug DVC remote
                    dvc remote list || echo "No DVC remotes configured"
                    
                    # Run DVC pull with verbose output
                    dvc pull -v || echo "DVC pull failed, check if DVC is initialized"
                    '''
                }
                
                echo "DVC pull completed"
            }
        }
        
        stage('Verify Data') {
            steps {
                sh '''
                echo "===== Verifying Data ====="
                # List directories that should contain data
                ls -la artifacts/ || echo "artifacts directory not found"
                
                # Check DVC files
                find . -name "*.dvc" -exec echo "DVC file: {}" \\; || echo "No DVC files found"
                
                # Activate the virtual environment and check DVC status
                . ${VENV_DIR}/bin/activate
                dvc status || echo "DVC status check failed"
                '''
            }
        }
    }
    
    post {
        success {
            echo "Pipeline executed successfully!"
        }
        failure {
            echo "Pipeline execution failed!"
            
            // Collect diagnostic information on failure
            sh '''
            echo "===== Diagnostic Information ====="
            
            echo "\\n===== Python Environment ====="
            python3 --version || echo "Python3 not available"
            pip3 --version || echo "Pip3 not available"
            
            echo "\\n===== Virtual Environment Status ====="
            ls -la ${VENV_DIR}/ || echo "venv directory not found"
            
            echo "\\n===== DVC Status ====="
            if [ -d ${VENV_DIR} ] && [ -f ${VENV_DIR}/bin/activate ]; then
                . ${VENV_DIR}/bin/activate && dvc status || echo "DVC command failed"
            else
                echo "Virtual environment not available for DVC status check"
            fi
            
            echo "\\n===== Last 20 lines of DVC logs ====="
            if [ -d .dvc/tmp/logs ]; then
                tail -n 20 .dvc/tmp/logs/* 2>/dev/null || echo "No DVC logs found"
            else
                echo "DVC logs directory not found"
            fi
            '''
        }
        always {
            // Clean up virtual environment (optional)
            sh 'rm -rf ${VENV_DIR} || true'
        }
    }
}
