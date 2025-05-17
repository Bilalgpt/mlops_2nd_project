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
    }
    
    post {
        success {
            echo "Pipeline executed successfully!"
        }
        failure {
            echo "Pipeline execution failed!"
        }
    }
}
