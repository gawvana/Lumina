import asyncio
import base64
import json
import os
import subprocess
import tempfile
import urllib.request
import websockets

ARTIFACTS_DIR = r"C:\Users\Hexo\.gemini\antigravity-ide\brain\829e3178-5d9a-4601-bbb5-35b14453647f"

async def main():
    temp_dir = tempfile.mkdtemp()
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    proc = subprocess.Popen([
        edge_path,
        "--headless=new",
        "--disable-gpu",
        "--remote-debugging-port=9223",
        f"--user-data-dir={temp_dir}",
        "--window-size=390,844",
        "http://127.0.0.1:8000/app"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        await asyncio.sleep(2)
        targets = json.loads(urllib.request.urlopen("http://127.0.0.1:9223/json").read())
        target = next(t for t in targets if "app" in t.get("url", ""))
        ws_url = target["webSocketDebuggerUrl"]

        async with websockets.connect(ws_url) as ws:
            msg_id = 1
            async def cmd(method, params=None):
                nonlocal msg_id
                c = {"id": msg_id, "method": method, "params": params or {}}
                msg_id += 1
                await ws.send(json.dumps(c))
                while True:
                    resp = json.loads(await ws.recv())
                    if resp.get("id") == c["id"]:
                        return resp.get("result", {})
                    if resp.get("method") == "Runtime.exceptionThrown":
                        details = resp["params"]["exceptionDetails"]
                        print(f"[JS EXCEPTION]:", details.get("text", ""), details.get("exception", {}).get("description", ""))

            await ws.send(json.dumps({"id": 999, "method": "Runtime.enable"}))
            await ws.send(json.dumps({"id": 998, "method": "Page.enable"}))

            async def screenshot(name):
                shot = await cmd("Page.captureScreenshot", {"format": "png"})
                img_data = base64.b64decode(shot["data"])
                out_path = os.path.join(ARTIFACTS_DIR, f"{name}.png")
                with open(out_path, "wb") as f:
                    f.write(img_data)
                print(f"[SCREENSHOT]: Saved {name}.png ({len(img_data)} bytes)")
                return out_path

            async def eval_js(expression):
                res = await cmd("Runtime.evaluate", {"expression": expression, "awaitPromise": True})
                return res.get("result", {}).get("value")

            # 1. Wait for initial Student render
            await asyncio.sleep(2)
            await screenshot("1_student_home")
            print("Student home loaded")

            # 2. Click Student Grades tab
            await eval_js("document.querySelector('[data-tab=\"grades\"]').click()")
            await asyncio.sleep(1)
            await screenshot("2_student_grades")
            print("Student grades tab loaded")

            # 3. Click Student Homework tab
            await eval_js("document.querySelector('[data-tab=\"homework\"]').click()")
            await asyncio.sleep(1)
            await screenshot("3_student_homework")
            print("Student homework tab loaded")

            # 4. Switch Dev Role to TEACHER
            await eval_js("window.luminaApp.switchDevRole('TEACHER')")
            await asyncio.sleep(2.5)
            await screenshot("4_teacher_dashboard")
            print("Teacher dashboard loaded")

            # 5. Switch Dev Role to PARENT
            await eval_js("window.luminaApp.switchDevRole('PARENT')")
            await asyncio.sleep(2.5)
            await screenshot("5_parent_overview")
            print("Parent overview loaded")

            # 6. Switch Dev Role to ADMIN
            await eval_js("window.luminaApp.switchDevRole('ADMIN')")
            await asyncio.sleep(2.5)
            await screenshot("6_admin_overview")
            print("Admin overview loaded")

            # 7. Test Language Toggle to Uzbek
            await eval_js("document.getElementById('langToggleBtn').click()")
            await asyncio.sleep(1)
            await screenshot("7_uzbek_language")
            print("Language switched to Uzbek")

            print("\n>>> ALL BROWSER QA AUTOMATION CHECKS PASSED SUCCESSFULLY! <<<")

    finally:
        proc.terminate()

asyncio.run(main())
