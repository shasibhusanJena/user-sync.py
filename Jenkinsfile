pipeline {
	agent any
	environment {
		a_variable = 'the variable'
	}
	stages {
		stage('Configure') {
			steps {
				script{
					echo "${a_variable}"
				}
			}
		}
		stage('Build') {
			steps {
				script{
					dir("user_sync") {
						sh 'echo hello'
						sh 'ls'
					}
					//dir("windows"){
						//archiveArtifacts artifacts: "$msi_file", fingerprint: true
						//archiveArtifacts artifacts: "$cert_file", fingerprint: true
					//}
				}
			}
		}
		//stage('Release') {
		//	when {expression { env.DO_RELEASE == 'true' }}
		//	steps {

		//		}
	//		}
	//	}
	}

	post { always { deleteDir()}}
}

