from flask import (
    Flask,
    request,
    send_from_directory
)

import os
import socket
import argparse
import shutil
import signal
import sys

app = Flask(__name__)

parser = argparse.ArgumentParser(description="Specify paths to upload")
parser.add_argument(
    "-fp", "--folderpath", type=str, help="Specify upload folder path", default="."
)
args = parser.parse_args()

UPLOAD_FOLDER = args.folderpath

# CTRL+C
def signal_handler(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib/28950776#28950776
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP

@app.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["files"]
        file.save(os.path.join(UPLOAD_FOLDER, file.filename))
        
    files = os.listdir(UPLOAD_FOLDER)
    files.sort()
    file_list = "<br>".join(
        [f'<a href="/downloads/{file}">{file}</a>' for file in files]
    )
    
    return f"""
        <!doctype html>
        <title>Upload and Download Files</title>
        <h1>Upload a File</h1>
        <div id="drop_area" style="padding:100px; border: 1px solid black">
            Drag and drop files here to upload
        </div>
        <input type="file" name="file_input" id="file_input">
        <button id="upload_button">Upload</button>
        <button id="cancel_button" style="display: none;">X</button>
        <div id="upload_progress"></div>
        <div id="speed"></div>
        <script>
        
        ['dragleave', 'drop', 'dragenter', 'dragover'].forEach(function (evt) {{
            document.addEventListener(evt, function (e) {{
                e.preventDefault();
            }}, false);
        }});
        var drop_area = document.getElementById('drop_area');
        var file_input = document.getElementById('file_input');
        var upload_button = document.getElementById('upload_button');
        var cancel_button = document.getElementById('cancel_button');
        var xhr = new XMLHttpRequest();
        drop_area.addEventListener('drop', function (e) {{
            e.preventDefault();
            file_input.files = e.dataTransfer.files;
        }}, false);
        upload_button.addEventListener('click', function (e) {{
            e.preventDefault();
            var fileList = file_input.files;
            if (fileList.length == 0) {{
                return false;
            }}
            xhr.open('post', '/', true);
            var lastTime = Date.now();
            var lastLoad = 0;
            xhr.upload.onprogress = function (event) {{
                if (event.lengthComputable) {{
                    var percent = Math.floor(event.loaded / event.total * 100);
                    document.getElementById('upload_progress').textContent = percent + '%';
                    var curTime = Date.now();
                    var curLoad = event.loaded;
                    var speed = ((curLoad - lastLoad) / (curTime - lastTime) / 1024).toFixed(2);
                    document.getElementById('speed').textContent = speed + 'MB/s'
                    lastTime = curTime;
                    lastLoad = curLoad;
                }}
            }};
            xhr.upload.onloadend = function (event) {{
                document.getElementById('upload_progress').textContent = 'File uploaded successfully';
                document.getElementById('speed').textContent = '0 MB/s';
                cancel_button.style.display = 'none';
            }};
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            var fd = new FormData();
            for (let file of fileList) {{
                fd.append('files', file);
            }}
            lastTime = Date.now();
            xhr.send(fd);
            cancel_button.style.display = 'inline';
        }}, false);
        cancel_button.addEventListener('click', function (e) {{
            xhr.abort();
            document.getElementById('upload_progress').textContent = '0%';
            document.getElementById('speed').textContent = '0 MB/s';
            cancel_button.style.display = 'none';
        }}, false);
        </script>
        <h1>Download a File</h1>
        {file_list}
        """

@app.route("/downloads/<path:filename>", methods=["GET", "POST"])
def download(filename):
    return send_from_directory(
        directory=UPLOAD_FOLDER,
        path=filename,
        as_attachment=True,
    )

if __name__ == "__main__":
    app.run(host=get_ip(), port=8080)
