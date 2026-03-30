name: Frociest Rumble - Build APK

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-22.04

    steps:

      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Installa dipendenze di sistema
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            build-essential git libffi-dev libssl-dev \
            zlib1g-dev liblzma-dev libbz2-dev libreadline-dev \
            libsqlite3-dev openjdk-17-jdk unzip autoconf libtool \
            pkg-config libltdl-dev cmake ninja-build \
            libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev

      # Java 17 richiesto da buildozer 1.5 + p4a + SDK 34.
      # Il runner ubuntu-22.04 parte con temurin-11: bisogna sovrascrivere.
      - name: Forza Java 17
        run: |
          sudo update-alternatives --set java \
            /usr/lib/jvm/java-17-openjdk-amd64/bin/java
          sudo update-alternatives --set javac \
            /usr/lib/jvm/java-17-openjdk-amd64/bin/javac
          echo "JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64" >> $GITHUB_ENV
          echo "/usr/lib/jvm/java-17-openjdk-amd64/bin" >> $GITHUB_PATH

      - name: Installa Buildozer e dipendenze Python
        run: |
          pip install --upgrade pip setuptools wheel
          pip install "cython==3.0.11"
          pip install "buildozer==1.5.0"
          pip install "python-for-android==2023.9.16"

      # buildozer 1.5 cerca sdkmanager in tools/bin/ (percorso legacy).
      # Le SDK tools moderne lo mettono in cmdline-tools/latest/bin/.
      # Soluzione: pre-installiamo cmdline-tools e creiamo il symlink legacy.
      - name: Pre-installa Android SDK cmdline-tools e symlink legacy
        run: |
          SDK_DIR="$HOME/.buildozer/android/platform/android-sdk"
          mkdir -p "$SDK_DIR/cmdline-tools"

          wget -q \
            https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip \
            -O /tmp/cmdline-tools.zip
          unzip -q /tmp/cmdline-tools.zip -d /tmp/cmdlt

          mv /tmp/cmdlt/cmdline-tools "$SDK_DIR/cmdline-tools/latest"

          mkdir -p "$SDK_DIR/tools/bin"
          ln -sf "$SDK_DIR/cmdline-tools/latest/bin/sdkmanager" \
                 "$SDK_DIR/tools/bin/sdkmanager"

          echo "ANDROID_SDK_ROOT=$SDK_DIR" >> $GITHUB_ENV
          echo "ANDROID_HOME=$SDK_DIR"     >> $GITHUB_ENV
          echo "$SDK_DIR/cmdline-tools/latest/bin" >> $GITHUB_PATH
          echo "$SDK_DIR/tools/bin"                >> $GITHUB_PATH

      - name: Accetta licenze Android SDK
        run: |
          mkdir -p "$HOME/.android"
          touch "$HOME/.android/repositories.cfg"

          SDK_DIR="$HOME/.buildozer/android/platform/android-sdk"
          mkdir -p "$SDK_DIR/licenses"

          printf "24333f8a63b6825ea9c5514f83c2829b004d1fee\n84831b9409646a918e30573bab4c9c91346d8abd\n" \
            > "$SDK_DIR/licenses/android-sdk-license"
          printf "d975f751698a77b662f1254ddbeed3901e976f5a\n" \
            > "$SDK_DIR/licenses/android-sdk-preview-license"
          printf "601085b94cd77f0b54ff86406957099ebe79c4d6\n" \
            > "$SDK_DIR/licenses/android-googletv-license"
          printf "33b6a2b64607f11b759f320ef9dff4ae5c47d97a\n" \
            > "$SDK_DIR/licenses/google-gdk-license"

          yes | "$SDK_DIR/cmdline-tools/latest/bin/sdkmanager" \
            --licenses --sdk_root="$SDK_DIR" || true

      - name: Cache Android SDK/NDK e build artifacts
        uses: actions/cache@v4
        with:
          path: |
            ~/.buildozer
            ~/.android
          # v4: cache key aggiornata dopo rimozione ffpyplayer
          key: buildozer-kivy-${{ hashFiles('buildozer.spec') }}-v4
          restore-keys: |
            buildozer-kivy-

      - name: Build APK
        run: |
          yes | buildozer -v android debug 2>&1 | tee build.log
          echo "Exit code: ${PIPESTATUS[1]}"

      - name: Mostra ultimi log in caso di errore
        if: failure()
        run: tail -400 build.log || true

      - name: Carica APK
        uses: actions/upload-artifact@v4
        with:
          name: FrociestRumble-beta
          path: bin/*.apk
          retention-days: 30

      - name: Carica log di build
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: build-log
          path: build.log
          retention-days: 7
