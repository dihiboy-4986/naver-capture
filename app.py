from flask import Flask, request, send_file, render_template_string
from playwright.sync_api import sync_playwright
import io
import zipfile

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>네이버 브랜드 광고 캡처</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 80px auto; padding: 20px; }
        h1 { color: #03c75a; }
        input { width: 100%; padding: 12px; font-size: 16px; margin: 10px 0; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; }
        button { width: 100%; padding: 14px; background: #03c75a; color: white; font-size: 16px; border: none; border-radius: 6px; cursor: pointer; }
        button:hover { background: #02a84a; }
        #status { margin-top: 20px; font-size: 15px; color: #555; }
    </style>
</head>
<body>
    <h1>📸 네이버 브랜드 광고 캡처</h1>
    <p>키워드를 입력하고 버튼을 누르면 PC/모바일 캡처 이미지를 다운로드합니다.</p>
    <input type="text" id="keyword" placeholder="예: 로로피아나" />
    <button onclick="capture()">캡처 시작</button>
    <div id="status"></div>
    <script>
        async function capture() {
            const keyword = document.getElementById('keyword').value.trim();
            if (!keyword) { alert('키워드를 입력해주세요!'); return; }
            document.getElementById('status').innerText = '캡처 중입니다... 잠시만 기다려주세요 ⏳';
            const res = await fetch('/capture', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({keyword})
            });
            if (res.ok) {
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = keyword + '_캡처.zip';
                a.click();
                document.getElementById('status').innerText = '✅ 다운로드 완료!';
            } else {
                document.getElementById('status').innerText = '❌ 오류가 발생했습니다. 다시 시도해주세요.';
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/capture', methods=['POST'])
def capture():
    keyword = request.json.get('keyword', '')
    url = f'https://search.naver.com/search.naver?query={keyword}'
    screenshots = {}

    with sync_playwright() as p:
        # PC 캡처
        browser = p.chromium.launch(args=['--font-render-hinting=none'])
        page = browser.new_page(viewport={'width': 1280, 'height': 900})
        page.goto(url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)
        screenshots['PC'] = page.screenshot(full_page=False, timeout=60000)
        browser.close()

        # 모바일 캡처
        browser = p.chromium.launch(args=['--font-render-hinting=none'])
        page = browser.new_page(
            viewport={'width': 390, 'height': 844},
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
        )
        page.goto(url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)

        # 브랜드 광고 안의 탭 버튼 찾기
        tabs = page.locator('.bottom_tab_button').all()

        if len(tabs) >= 2:
            for i, tab in enumerate(tabs[:3]):
                try:
                    tab.click()
                    page.wait_for_timeout(1500)
                    screenshots[f'모바일_탭{i+1}'] = page.screenshot(full_page=False, timeout=60000)
                except:
                    pass
        else:
            screenshots['모바일'] = page.screenshot(full_page=False, timeout=60000)

        browser.close()

    # ZIP으로 묶어서 전달
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for name, data in screenshots.items():
            zf.writestr(f'{keyword}_{name}.png', data)
    zip_buffer.seek(0)

    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name=f'{keyword}_캡처.zip')

if __name__ == '__main__':
    app.run(debug=True)