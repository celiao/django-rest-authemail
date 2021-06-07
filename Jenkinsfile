pipeline {
    agent any
    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        quietPeriod(5)
    }
    stages {
        stage('Checkout') {
            steps {
                script {
                    def scmVars = checkout scm

                    env.RELEASE_BRANCH = "master"
                    env.GIT_COMMIT = scmVars.GIT_COMMIT
                }
            }
        }

        stage('Release') {
            when {
                branch env.RELEASE_BRANCH
            }
            environment {
                GIT_AUTH = credentials('github-username-and-token')
                PYPI_AUTH = credentials('pypicloud-dev')
                PYPI_URL = env.INTERNAL_PYPI
            }
            steps {
                script {
                    sh "GH_TOKEN=\$GIT_AUTH_PSW npx semantic-release"
                }
            }
        }
    }
}

