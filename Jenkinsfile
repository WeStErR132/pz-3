pipeline {
    agent any
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
    }
    
    parameters {
        string(name: 'STUDENT_NAME', defaultValue: 'Иванов Иван', description: 'ФИО студента')
        choice(name: 'ENVIRONMENT', choices: ['dev', 'staging', 'production'], description: 'Среда')
        string(name: 'PORT', defaultValue: '8081', description: 'Порт')
        booleanParam(name: 'RUN_TESTS', defaultValue: true, description: 'Запускать тесты?')
        booleanParam(name: 'PUSH_TO_REGISTRY', defaultValue: false, description: 'Push в Docker Hub?')
    }
    
    environment {
        DOCKER_HUB_USER = 'westerr132'
        DOCKER_IMAGE = "${DOCKER_HUB_USER}/student-app:${BUILD_NUMBER}"
        CONTAINER_NAME = "student-app-${params.ENVIRONMENT}-${BUILD_NUMBER}"
        TELEGRAM_TOKEN = credentials('8775351224:AAHwV0tgc3bj-psNmPRal_6S-IOoqcgJBkA')
        TELEGRAM_CHAT_ID = credentials('877753874')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'ls -la'
            }
        }
        
        stage('Setup Python') {
            when { expression { params.RUN_TESTS } }
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('Run Tests') {
            when { expression { params.RUN_TESTS } }
            steps {
                sh '''
                    . venv/bin/activate
                    python -m unittest test_app.py -v
                '''
            }
        }
        
        stage('Build Docker') {
            steps {
                sh "docker build -t ${DOCKER_IMAGE} --no-cache ."
                sh "docker tag ${DOCKER_IMAGE} ${DOCKER_HUB_USER}/student-app:latest"
            }
        }
        
        stage('Push to Registry') {
            when { expression { params.PUSH_TO_REGISTRY } }
            steps {
                script {
                    docker.withRegistry('', 'docker-hub-credentials') {
                        docker.image("${DOCKER_IMAGE}").push()
                        docker.image("${DOCKER_IMAGE}").push('latest')
                    }
                }
            }
        }
        
        stage('Deploy') {
            steps {
                script {
                    // Остановка старых контейнеров
                    sh "docker ps -aq --filter name=student-app-${params.ENVIRONMENT} | xargs -r docker stop 2>/dev/null || true"
                    sh "docker ps -aq --filter name=student-app-${params.ENVIRONMENT} | xargs -r docker rm 2>/dev/null || true"
                    
                    // Запуск нового
                    def deployPort = params.ENVIRONMENT == 'production' ? '80' : params.PORT
                    sh """
                        docker run -d \
                            --name ${CONTAINER_NAME} \
                            --restart unless-stopped \
                            -p ${deployPort}:5000 \
                            -e STUDENT_NAME='${params.STUDENT_NAME}' \
                            -e ENVIRONMENT='${params.ENVIRONMENT}' \
                            -e BUILD_NUMBER='${BUILD_NUMBER}' \
                            ${DOCKER_IMAGE}
                    """
                    
                    sleep 5
                    sh "curl -f http://localhost:${deployPort}/health || true"
                    
                    def serverIp = sh(script: "hostname -I | awk '{print \\$1}'", returnStdout: true).trim()
                    echo "Deployed to http://${serverIp}:${deployPort}"
                }
            }
        }
        
        stage('Production Approval') {
            when { expression { params.ENVIRONMENT == 'production' } }
            steps {
                input message: "Deploy to PRODUCTION?", ok: "Yes, deploy"
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            script {
                def msg = "✅ Build SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER} (${params.ENVIRONMENT})"
                sh "curl -s -X POST 'https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage' -d 'chat_id=${TELEGRAM_CHAT_ID}' -d 'text=${msg}'"
            }
        }
        failure {
            script {
                def msg = "❌ Build FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER} (${params.ENVIRONMENT})"
                sh "curl -s -X POST 'https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage' -d 'chat_id=${TELEGRAM_CHAT_ID}' -d 'text=${msg}'"
            }
        }
    }
}
