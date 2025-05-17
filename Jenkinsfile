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
                
                echo "\\n===== Python Environment Variables ====="
                env | grep -i python
                
                echo "\\n===== Directory Structure ====="
                ls -la
                
                echo "\\n===== setup.py Content ====="
                cat setup.py
                
                echo "\\n===== requirements.txt Content ====="
                cat requirements.txt
                '''
            }
        }
        
        stage('Create Virtual Environment') {
            steps {
                sh '''
                echo "===== Creating Virtual Environment ====="
                # Remove any existing venv directory
                rm -rf venv || true
                
                # Create a new virtual environment
                python3 -m venv venv
                
                # Verify venv creation
                ls -la venv/
                '''
                
                echo "Virtual environment created"
            }
        }
        
        stage('Install Dependencies') {
            steps {
                sh '''
                echo "===== Installing Dependencies ====="
                # Activate the virtual environment
                . venv/bin/activate
                
                # Upgrade pip
                pip install --upgrade pip
                
                # Install the package in development mode using setup.py
                pip install -e .
                
                # Verify installed packages
                pip list
                '''
                
                echo "Dependencies installed successfully"
            }
        }
        
        stage('DVC Setup') {
            steps {
                sh '''
                echo "===== Setting up DVC ====="
                # Activate the virtual environment
                . venv/bin/activate
                
                # Install DVC with Google Cloud support
                pip install dvc dvc[gs]
                
                # Verify DVC installation
                dvc --version
                
                # Check DVC configuration
                cat .dvc/config || echo "DVC config not found"
                '''
            }
        }
        
        stage('DVC Pull') {
            steps {
                // Use the GCP-KEY credential for DVC authentication
                withCredentials([file(credentialsId: 'GCP-KEY', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh '''
                    echo "===== Running DVC Pull ====="
                    # Activate the virtual environment
                    . venv/bin/activate
                    
                    # Set the Google credentials
                    export GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS
                    echo "Credentials file exists: $(test -f $GOOGLE_APPLICATION_CREDENTIALS && echo 'Yes' || echo 'No')"
                    
                    # Debug DVC remote
                    dvc remote list
                    
                    # Run DVC pull with verbose output
                    dvc pull -v
                    '''
                }
                
                echo "DVC pull completed successfully"
            }
        }
        
        stage('Verify Data') {
            steps {
                sh '''
                echo "===== Verifying Data ====="
                # List directories that should contain data
                ls -la artifacts/ || echo "artifacts directory not found"
                
                # Check DVC files
                find . -name "*.dvc" -exec echo "DVC file: {}" \\;
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
            python3 --version
            pip3 --version
            
            echo "\\n===== Virtual Environment Status ====="
            ls -la venv/ || echo "venv directory not found"
            
            echo "\\n===== DVC Status ====="
            . venv/bin/activate && dvc status || echo "DVC command failed"
            
            echo "\\n===== Last 20 lines of DVC logs ====="
            tail -n 20 .dvc/tmp/logs/* 2>/dev/null || echo "No DVC logs found"
            '''
        }
        always {
            // Clean up virtual environment (optional)
            sh 'rm -rf venv || true'
        }
    }
}
