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
                env | grep -i python || echo "No Python environment variables found"
                
                echo "\\n===== Directory Structure ====="
                ls -la
                
                echo "\\n===== setup.py Content ====="
                cat setup.py || echo "setup.py not found"
                
                echo "\\n===== requirements.txt Content ====="
                cat requirements.txt || echo "requirements.txt not found"
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
                
                # Check if setup.py exists and install from it, otherwise use requirements.txt
                if [ -f setup.py ]; then
                    echo "Installing from setup.py"
                    pip install -e .
                elif [ -f requirements.txt ]; then
                    echo "Installing from requirements.txt"
                    pip install -r requirements.txt
                else
                    echo "Neither setup.py nor requirements.txt found"
                    exit 1
                fi
                
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
            ls -la venv/ || echo "venv directory not found"
            
            echo "\\n===== DVC Status ====="
            if [ -d venv ] && [ -f venv/bin/activate ]; then
                . venv/bin/activate && dvc status || echo "DVC command failed"
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
            sh 'rm -rf venv || true'
        }
    }
}
