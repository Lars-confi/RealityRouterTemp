import re

with open('reality-router/src/router/metrics.py', 'r') as f:
    content = f.read()

# 1. Title replacement
old_title = '<h1 style="text-align: center; margin-bottom: 40px; letter-spacing: 2px;">REALITY ROUTER CONTROL CENTER</h1>'
new_title = '''<div style="text-align: center; margin-bottom: 40px;">
                <h1 style="display: inline-block; margin-bottom: 5px; letter-spacing: 2px;">REALITY ROUTER CONTROL CENTER</h1>
                <div id="version-badge" style="font-size: 0.85em; color: #8b949e; margin-top: 5px;">Version: <span id="current-version">1.0.0</span></div>
                <div id="update-alert" style="display: none; margin-top: 10px; color: #f39c12; font-weight: bold; background: rgba(243, 156, 18, 0.1); padding: 5px 15px; border-radius: 5px; border: 1px solid rgba(243, 156, 18, 0.3);">
                    ⚠️ A new version is available! Run the installer to update.
                </div>
            </div>'''
content = content.replace(old_title, new_title)

# 2. Check version script insertion
old_js = '''            initPreferences();

            async function loadData() {'''

new_js = '''            initPreferences();

            async function checkVersion() {
                try {
                    const response = await fetch('https://raw.githubusercontent.com/Lars-confi/RealityRouterTemp/main/reality-router/src/main.py');
                    const text = await response.text();
                    const match = text.match(/version="([^"]+)"/);
                    if (match) {
                        const latestVersion = match[1];
                        const currentVersion = document.getElementById('current-version').innerText;
                        if (latestVersion !== currentVersion) {
                            document.getElementById('update-alert').style.display = 'inline-block';
                        }
                    }
                } catch (e) {
                    console.error("Failed to check version", e);
                }
            }
            checkVersion();

            async function loadData() {'''

content = content.replace(old_js, new_js)

# 3. Cross emoji to lightbulb replacement
old_td = "<td style=\"padding: 4px; text-align: center;\">${d.feedback_required ? '❌' : ''}</td>"
new_td = "<td style=\"padding: 4px; text-align: center;\">${d.feedback_required ? '💡' : ''}</td>"

content = content.replace(old_td, new_td)

with open('reality-router/src/router/metrics.py', 'w') as f:
    f.write(content)

