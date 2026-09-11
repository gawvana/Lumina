import asyncio
import json
import os
import subprocess
import tempfile
import urllib.request
import websockets

async def run_qa():
    temp_dir = tempfile.mkdtemp()
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    proc = subprocess.Popen([
        edge_path,
        "--headless=new",
        "--disable-gpu",
        "--remote-debugging-port=9222",
        f"--user-data-dir={temp_dir}",
        "--window-size=390,844",
        "http://127.0.0.1:8000/app"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        await asyncio.sleep(2)
        # Query target
        targets = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read())
        print(f"Found {len(targets)} targets")
        target = next(t for t in targets if "app" in t.get("url", ""))
        ws_url = target["webSocketDebuggerUrl"]
        print(f"Connecting to CDP: {ws_url}")

        async with websockets.connect(ws_url) as ws:
            msg_id = 1
            async def send_cmd(method, params=None):
                nonlocal msg_id
                cmd = {"id": msg_id, "method": method, "params": params or {}}
                msg_id += 1
                await ws.send(json.dumps(cmd))
                while True:
                    resp = json.loads(await ws.recv())
                    if resp.get("id") == cmd["id"]:
                        return resp.get("result", {})
                    if resp.get("method") == "Runtime.consoleAPICalled":
                        args = [str(a.get("value", a.get("description", ""))) for a in resp["params"]["args"]]
                        print(f"[BROWSER CONSOLE {resp['params']['type']}]:", " ".join(args))
                    elif resp.get("method") == "Runtime.exceptionThrown":
                        details = resp["params"]["exceptionDetails"]
                        print(f"[BROWSER EXCEPTION]:", details.get("text", ""), details.get("exception", {}).get("description", ""))

            await ws.send(json.dumps({"id": 999, "method": "Runtime.enable"}))
            await ws.send(json.dumps({"id": 998, "method": "Console.enable"}))
            await ws.send(json.dumps({"id": 997, "method": "Page.enable"}))

            # Wait 3 seconds to let JS initialize and network requests finish
            for _ in range(30):
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=0.1)
                    resp = json.loads(raw)
                    if resp.get("method") == "Runtime.consoleAPICalled":
                        args = [str(a.get("value", a.get("description", ""))) for a in resp["params"]["args"]]
                        print(f"[BROWSER CONSOLE {resp['params']['type']}]:", " ".join(args))
                    elif resp.get("method") == "Runtime.exceptionThrown":
                        details = resp["params"]["exceptionDetails"]
                        print(f"[BROWSER EXCEPTION]:", details.get("text", ""), details.get("exception", {}).get("description", ""))
                except asyncio.TimeoutError:
                    pass

            # Inspect DOM content of viewContainer
            res = await send_cmd("Runtime.evaluate", {
                "expression": "document.getElementById('viewContainer').innerHTML.substring(0, 500)"
            })
            print("[VIEW CONTAINER INNER HTML]:", res.get("result", {}).get("value"))

            # Capture screenshot of rendered Student View
            shot = await send_cmd("Page.captureScreenshot", {"format": "png"})
            import base64
            img_data = base64.b64decode(shot["data"])
            out_img = r"C:\Users\Hexo\.gemini\antigravity-ide\brain\829e3178-5d9a-4601-bbb5-35b14453647f\student_view_rendered.png"
            with open(out_img, "wb") as f:
                f.write(img_data)
            print(f"[SCREENSHOT SAVED]: {out_img} ({len(img_data)} bytes)")

    finally:
        proc.terminate()

asyncio.run(run_qa())
