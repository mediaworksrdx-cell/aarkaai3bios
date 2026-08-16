# GitHub Secrets Setup for Android CI/CD

This document details the configuration of GitHub Secrets required for automated, secure building and signing of the AARKAAI Android application in CI/CD pipelines.

---

## 1. Overview

Committing signing keys (`.jks`, `.keystore`), keystore passwords, and production secrets directly to version control creates severe security vulnerabilities. If repository access is compromised or the project is made public, unauthorized parties could sign malicious application updates or access backend infrastructure.

To ensure security:
- **Keystores and credentials** are stored encrypted in **GitHub Actions Secrets**.
- **`gradle.properties`** with sensitive credentials stays on the local developer machine and is excluded from git via `.gitignore`.
- **`gradle.properties.example`** and **`gradle.properties.secure`** act as committed, safe template files.
- CI/CD pipelines dynamically decode the keystore and inject secret properties during the build step.

---

## 2. Configuring Secrets in GitHub

To add secrets to your GitHub repository:

1. Navigate to your repository on GitHub.
2. Go to **Settings** > **Secrets and variables** > **Actions**.
3. Under **Repository secrets**, click **New repository secret**.
4. Create each secret listed below with its corresponding value.

### Required Secrets

| Secret Name | Description | Example / Generation Command |
| :--- | :--- | :--- |
| `RELEASE_KEYSTORE_BASE64` | Base64-encoded string of `release.jks` | See encoding commands below |
| `RELEASE_STORE_PASSWORD` | Password for the release keystore | `your_keystore_password` |
| `RELEASE_KEY_ALIAS` | Key alias within the keystore | `aarkaai_key` |
| `RELEASE_KEY_PASSWORD` | Password for the specific key alias | `your_key_password` |
| `AARKAAI_BACKEND_URL` | Production backend base URL | `http://43.204.153.162:5000/` |

---

## 3. How to Generate `RELEASE_KEYSTORE_BASE64`

Run one of the following commands from your project root to convert your keystore file into a Base64 string:

### macOS / Linux
```bash
base64 -i android-app/release.jks | tr -d '\n'
```
*Alternatively (Linux GNU base64):*
```bash
base64 -w 0 android-app/release.jks
```

### Windows (PowerShell)
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("android-app\release.jks")) | Set-Clipboard
```
*(This copies the encoded Base64 string directly to your clipboard.)*

---

## 4. How the CI/CD Workflow Uses Secrets

In GitHub Actions workflows, secrets are injected at build time without persisting in repository code:

```yaml
- name: Set up JDK 17
  uses: actions/setup-java@v4
  with:
    java-version: '17'
    distribution: 'temurin'

- name: Restore Signing Keystore
  run: |
    echo "${{ secrets.RELEASE_KEYSTORE_BASE64 }}" | base64 --decode > android-app/release.jks

- name: Configure gradle.properties
  run: |
    cat <<EOF > android-app/gradle.properties
    org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
    android.useAndroidX=true
    kotlin.code.style=official
    android.nonTransitiveRClass=true

    RELEASE_STORE_FILE=../release.jks
    RELEASE_STORE_PASSWORD=${{ secrets.RELEASE_STORE_PASSWORD }}
    RELEASE_KEY_ALIAS=${{ secrets.RELEASE_KEY_ALIAS }}
    RELEASE_KEY_PASSWORD=${{ secrets.RELEASE_KEY_PASSWORD }}

    AARKAAI_BASE_URL=${{ secrets.AARKAAI_BACKEND_URL }}
    EOF

- name: Build Release APK / Bundle
  run: |
    cd android-app
    ./gradlew assembleRelease
```

---

## 5. Local Development vs. CI/CD

- **Safe Templates (Committed)**:
  - `android-app/gradle.properties.example` &mdash; Safe reference template for developers.
  - `android-app/gradle.properties.secure` &mdash; Parameterized template for automated builds.
- **Local Development (`android-app/gradle.properties`)**:
  - Developers copy `gradle.properties.example` to `gradle.properties` and fill in local or staging values.
  - `gradle.properties` is ignored by `.gitignore` and must **never** be committed.
