output_dir = dist
signed_dir = signed
output_filename = user-sync
prebuilt_dir = external

# Signing
userid = ustinst1
ruleid = 42992
keypath = sehkmet
password_var = INSTALLER_SIGN_PASS
bast_url = https://artifactory.corp.adobe.com/artifactory/maven-est-public-release/com/adobe/est/clients/bast-client/1.0.119/bast-client-1.0.119-standalone.jar
bast_path = BastClient.jar
artifactory_user = dmenpm
artifactory_key_var = ARTIFACTORY_KEY

ifeq ($(OS),Windows_NT)
	rm_path := $(shell python -c "import distutils.spawn; print(distutils.spawn.find_executable('rm'))")
    ifeq ($(rm_path),None)
        RM := rmdir /S /Q
    else
	    RM := $(rm_path) -rf
    endif
else
    RM := rm -rf
endif

standalone:
	python -m pip install --upgrade pip
	python -m pip install --upgrade pyinstaller
	python -m pip install --upgrade setuptools
	-$(RM) $(output_dir)
	python .build/pre_build.py
	pyinstaller --clean --noconfirm user-sync.spec

test:
	nosetests --no-byte-compile tests

sign:
	@rm ${signed_dir} -rf
	@mkdir ${signed_dir}
	mv ${output_dir}\user-sync.exe ${output_dir}\AdobeUSTSetup.exe
	curl -u ${artifactory_user}:${${artifactory_key_var}} -X GET ${bast_url} -o ${bast_path}
	java -jar "${bast_path}" -s -b "${output_dir}" -d "${signed_dir}" -ri "${ruleid}" -u "${userid}" -p "${${password_var}}" -k "${keypath}"
	mv ${signed_dir}\AdobeUSTSetup.exe ${signed_dir}\user-sync.exe