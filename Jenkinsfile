pipeline {
    agent any
    
    environment {
        VENV_DIR = "${WORKSPACE}/venv"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scmGit(
                    branches: [[name: '*/main']], 
                    extensions: [], 
                    userRemoteConfigs: [[
                        credentialsId: 'github-token-2nd-project', 
                        url: 'https://github.com/Bilalgpt/mlops_2nd_project.git'
                    ]]
                )
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
                
                echo "\\n===== Directory Structure ====="
                ls -la
                '''
            }
        }
        
        stage("Install Python Environment") {
            steps {
                sh '''
                echo "===== Installing python3-venv ====="
                # Try using sudo to install python3-venv
                sudo apt-get update -y || echo "Cannot update apt repositories"
                sudo apt-get install -y python3-venv || echo "Cannot install python3-venv, will try alternative approach"
                '''
            }
        }
        
        stage("Create Virtual Environment") {
            steps {
                sh '''
                echo "===== Creating Virtual Environment ====="
                # If python3-venv is successfully installed
                if command -v python3 -m venv &> /dev/null; then
                    rm -rf ${VENV_DIR} || true
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -e .
                    pip install dvc dvc[gs]
                else
                    # Fallback to user-install without venv
                    echo "Using pip user install instead of venv"
                    pip3 install --user --upgrade pip
                    pip3 install --user -e .
                    pip3 install --user dvc dvc[gs]
                    export PATH=$HOME/.local/bin:$PATH
                fi
                '''
            }
        }
        
        // Rest of the pipeline stages...
    }
}
