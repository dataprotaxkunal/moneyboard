1. Put your Moneyboard index.html in this folder (next to package.json).
2. On github.com: New repository (any name, Public or Private) > "uploading an existing file".
3. Drag in everything: index.html, make_app.py, prep_web.py, package.json, capacitor.config.json,
   and the .github folder (drag the folder itself so .github/workflows/build-apk.yml is kept).
   Commit to the main branch.
4. Actions tab > "Build APK" > Run workflow. ~5 min later open the run and download "Moneyboard-APK".
5. Unzip, send app-debug.apk to your phone, install (allow unknown apps).
Login problem in the app? Firebase console > Authentication > Settings > Authorized domains > add localhost.
