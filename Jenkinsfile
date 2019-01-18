node {
    stage ('Prepare') {
        checkout scm
    }
    stage('Build') {
        sh './run.sh commit'
    }
}
