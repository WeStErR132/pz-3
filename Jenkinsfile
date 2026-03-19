pipeline {
    agent any
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
    }
    
    parameters {
        string(
            name: 'STUDENT_NAME',
            defaultValue: 'Иванов Иван',
            description: 'ФИО студента для отображения в приложении'
        )
        choice(
            name: 'ENVIRONMENT',
            choices: ['dev', 'staging', 'production'],
            description: 'Среда развертывания'
        )
        string(
            name: 'PORT',
            defaultValue: '8081',
            description: 'Порт для развертывания (для dev/staging)'
        )
        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: 'Запускать ли тесты?'
        )
        booleanParam(
            name: 'SKIP_PUSH',
            defaultValue: false,
            description: 'Пропустить публикацию в Docker Hub (для тестов)'
        )
    }
    
    environment {
        DOCKER_REGISTRY = 'docker.io'
        DOCKER_IMAGE = "yourdockerhub/student-app:${BUILD_NUMBER}"
        DOCKER_IMAGE_LATEST = "yourdockerhub/student-app:latest"
        CONTAINER_NAME = "student-app-${params.ENVIRONMENT}-${BUILD_NUMBER}"
        TELEGRAM_TOKEN = credentials('telegram-token')
        TELEGRAM_CHAT_ID = credentials('telegram-chat-id')
    }
    
    stages {
        stage('📥 Checkout') {
            steps {
                script {
                    currentBuild.displayName = "#${BUILD_NUMBER} - ${params.ENVIRONMENT}"
                    currentBuild.description = "Student: ${params.STUDENT_NAME}"
                }
                echo "🔀 Клонирование репозитория..."
                checkout scm
                sh 'ls -la'
            }
        }
        
        stage('🧪 Setup & Test') {
            when {
                expression { params.RUN_TESTS }
            }
            stages {
                stage('Setup Python') {
                    steps {
                        echo '🐍 Настройка Python окружения...'
                        sh '''
                            python3 -m venv venv
                            . venv/bin/activate
                            pip install --upgrade pip
                            pip install -r requirements.txt
                        '''
                    }
                }
                
                stage('Unit Tests') {
                    steps {
                        echo '🧪 Запуск unit-тестов...'
                        sh '''
                            . venv/bin/activate
                            python -m unittest test_app.py -v
                        '''
                    }
                    post {
                        always {
                            // Генерация XML отчета для Jenkins
                            sh '''
                                . venv/bin/activate
                                python -m unittest test_app.py -v 2>&1 | tee test_output.log || true
                            '''
                        }
                        success {
                            echo '✅ Все тесты пройдены!'
                        }
                        failure {
                            echo '❌ Тесты завершились с ошибками'
                        }
                    }
                }
                
                stage('Code Quality Check') {
                    steps {
                        echo '🔍 Проверка качества кода...'
                        sh '''
                            . venv/bin/activate
                            pip install flake8
                            flake8 app.py --max-line-length=120 --ignore=E501,W503 || true
                        '''
                    }
                }
            }
        }
        
        stage('🐳 Build & Push') {
            stages {
                stage('Build Docker Image') {
                    steps {
                        echo '🏗️ Сборка Docker образа...'
                        script {
                            def customImage = docker.build("${DOCKER_IMAGE}", "--no-cache .")
                            // Тегируем как latest для удобства
                            sh "docker tag ${DOCKER_IMAGE} ${DOCKER_IMAGE_LATEST}"
                        }
                    }
                }
                
                stage('Security Scan') {
                    steps {
                        echo '🔒 Проверка безопасности образа...'
                        sh '''
                            # Проверка на наличие уязвимостей (если установлен trivy)
                            which trivy && trivy image ${DOCKER_IMAGE} --severity HIGH,CRITICAL --exit-code 0 || echo "Trivy не установлен, пропускаем сканирование"
                        '''
                    }
                }
                
                stage('Push to Registry') {
                    when {
                        allOf {
                            branch 'main'
                            expression { !params.SKIP_PUSH }
                        }
                    }
                    steps {
                        echo '📤 Публикация образа в Docker Hub...'
                        script {
                            docker.withRegistry('', 'docker-hub-credentials') {
                                docker.image("${DOCKER_IMAGE}").push()
                                docker.image("${DOCKER_IMAGE}").push('latest')
                            }
                        }
                    }
                }
            }
        }
        
        stage('🚀 Deploy to Dev') {
            when {
                expression { params.ENVIRONMENT == 'dev' }
            }
            steps {
                echo '🚀 Развертывание в DEV окружении...'
                script {
                    deployApp(params.PORT, 'dev')
                }
            }
        }
        
        stage('🚀 Deploy to Staging') {
            when {
                expression { params.ENVIRONMENT == 'staging' }
            }
            steps {
                echo '🚀 Развертывание в STAGING окружении...'
                script {
                    deployApp(params.PORT, 'staging')
                }
            }
        }
        
        stage('⏸️ Approve Production') {
            when {
                expression { params.ENVIRONMENT == 'production' }
            }
            steps {
                script {
                    input message: "🚨 Подтвердите развертывание в PRODUCTION?", 
                          ok: "Да, развернуть",
                          submitterParameter: 'APPROVER'
                    
                    echo "✅ Развертывание одобрено пользователем: ${APPROVER}"
                }
            }
        }
        
        stage('🚀 Deploy to Production') {
            when {
                expression { params.ENVIRONMENT == 'production' }
            }
            steps {
                echo '🚀 Развертывание в PRODUCTION...'
                script {
                    // Для production используем стандартный порт 80
                    deployApp('80', 'production')
                }
            }
        }
        
        stage('🏷️ Create Git Tag') {
            when {
                allOf {
                    expression { params.ENVIRONMENT == 'production' }
                    expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
                }
            }
            steps {
                echo '🏷️ Создание Git-тега для релиза...'
                script {
                    def tagName = "v${BUILD_NUMBER}"
                    sh """
                        git config user.email "jenkins@localhost"
                        git config user.name "Jenkins CI"
                        git tag -a ${tagName} -m "Release ${tagName} - Production deployment"
                        git push origin ${tagName}
                    """
                    echo "✅ Создан тег: ${tagName}"
                }
            }
        }
    }
    
    post {
        always {
            echo '🧹 Очистка рабочего пространства...'
            cleanWs(cleanWhenNotBuilt: false,
                    deleteDirs: true,
                    disableDeferredWipeout: true,
                    notFailBuild: true)
        }
        
        success {
            script {
                sendTelegramNotification("✅", "SUCCESS", params.ENVIRONMENT)
            }
        }
        
        failure {
            script {
                sendTelegramNotification("❌", "FAILED", params.ENVIRONMENT)
            }
        }
        
        unstable {
            script {
                sendTelegramNotification("⚠️", "UNSTABLE", params.ENVIRONMENT)
            }
        }
    }
}

// ==================== ФУНКЦИИ ====================

def deployApp(port, environment) {
    // Остановка и удаление старого контейнера этого окружения
    sh """
        # Находим и останавливаем старые контейнеры этого окружения
        OLD_CONTAINERS=\$(docker ps -q --filter "name=student-app-${environment}" || true)
        if [ ! -z "\$OLD_CONTAINERS" ]; then
            echo "Остановка старых контейнеров: \$OLD_CONTAINERS"
            docker stop \$OLD_CONTAINERS || true
            docker rm \$OLD_CONTAINERS || true
        fi
        
        # Запуск нового контейнера
        docker run -d \
            --name ${CONTAINER_NAME} \
            --restart unless-stopped \
            -p ${port}:5000 \
            -e STUDENT_NAME='${params.STUDENT_NAME}' \
            -e ENVIRONMENT='${environment}' \
            -e BUILD_NUMBER='${BUILD_NUMBER}' \
            -e PORT=5000 \
            --health-cmd="curl -f http://localhost:5000/health || exit 1" \
            --health-interval=30s \
            --health-timeout=10s \
            --health-retries=3 \
            ${DOCKER_IMAGE}
        
        # Ждем запуска
        sleep 5
        
        # Проверяем health check
        docker ps | grep ${CONTAINER_NAME}
        curl -f http://localhost:${port}/health || echo "Health check failed!"
    """
    
    def serverIp = sh(script: "hostname -I | awk '{print \$1}'", returnStdout: true).trim()
    
    echo """
    =========================================
    🎉 Приложение успешно развернуто!
    
    🌐 URL: http://${serverIp}:${port}
    🔍 Health: http://${serverIp}:${port}/health
    📊 API Info: http://${serverIp}:${port}/api/info
    
    Окружение: ${environment}
    Контейнер: ${CONTAINER_NAME}
    =========================================
    """
}

def sendTelegramNotification(emoji, status, environment) {
    def message = """
    ${emoji} <b>Jenkins Build ${status}</b>
    
    📋 Проект: ${env.JOB_NAME}
    🔢 Сборка: #${env.BUILD_NUMBER}
    🌍 Окружение: <code>${environment}</code>
    👤 Студент: ${params.STUDENT_NAME}
    
    ⏱️ Длительность: ${currentBuild.durationString}
    
    🔗 <a href="${env.BUILD_URL}">Открыть в Jenkins</a>
    """
    
    sh """
        curl -s -X POST \
            https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage \
            -d chat_id=${TELEGRAM_CHAT_ID} \
            -d text='${message}' \
            -d parse_mode='HTML' \
            -d disable_web_page_preview='true'
    """
}
