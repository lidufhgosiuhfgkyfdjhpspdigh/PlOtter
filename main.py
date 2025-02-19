from flask import Flask, render_template, request, jsonify, send_file
from custom import bg
import os
import subprocess
import requests
import signal
import sys
import json
import base64
from io import BytesIO

app = Flask(__name__)

# Starte den pigpio-Daemon, wenn er nicht bereits läuft
if not os.path.exists("/var/run/pigpio.pid"):
    subprocess.run(["sudo", "pigpiod"], check=True)
executing = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/printImage', methods=['POST'])
def printImage():
    try:
        data = request.json
        lines = data['lines']
        lines = lines[0]
        bg.plot_lines(lines)
        bg.quiet(servos=[14, 15, 18]) #Stimmen die Servo-Nummern?
        result = "Bild ist fertig"
        print(result)
        return result
    except Exception as e:
        return str(e)

@app.route('/stopPrinting', methods=['POST'])
def stopPrinting():
    global executing
    if executing:
        bg.quiet(servos=[14][15][18])
        executing = False
        return "Druckvorgang abgebrochen"
    else:
        return "Aktuell wird nicht gedruckt"

@app.route('/generate_ai', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        sketch_data_url = data['sketch']
        prompt = data['prompt']
        withDrawing = data['withDrawing']
        
        if prompt is None:
            return jsonify({"error": "No prompt"}), 400
        
        # Log the prompt
        print(f"Prompt: {prompt}")
        
        # Übersetzen des Prompts ins Englisch
        urlT = "https://translate.terraprint.co/translate"
        data = {
            "q": prompt,
            "source": "auto",
            "target": "en"
        }
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(urlT, data=json.dumps(data), headers=headers)
        prompt = response.json()["translatedText"]

        print(f"Englischer prompt: {prompt}")

        if withDrawing:
            print(f"With Drawing")
            sketch_data = sketch_data_url.split(',')[1]
            sketch_file = BytesIO(base64.b64decode(sketch_data))
            
            api_key = 'abc'
            api_url = 'https://clipdrop-api.co/sketch-to-image/v1/sketch-to-image'
            
            files = {'sketch_file': sketch_file}
            data = {'prompt': prompt}
            headers = {'x-api-key': api_key}
            
            response = requests.post(api_url, files=files, data=data, headers=headers)
            
            if response.status_code != 200:
                raise Exception("Non-200 response: " + str(response.text))

            image_data = base64.b64encode(response.content).decode('utf-8')
            image_data_list = [image_data]

            return jsonify({"image_data_list": image_data_list})
        
        else:
            print(f"Without drawing")
            url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

            body = {
            "steps": 40,
            "width": 1024,
            "height": 1024,
            "seed": 0,
            "cfg_scale": 5,
            "samples": 1,
            "text_prompts": [
                {
                "text": prompt,
                "weight": 1
                },
                {
                "text": " ",
                "weight": -1
                }
            ],
            }

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": "Bearer sk-",
            }

            response = requests.post(
                url,
                headers=headers,
                json=body,
            )

            '''
            response = requests.post(
                f"https://api.stability.ai/v2beta/stable-image/generate/core",
                headers={
                    "authorization": f"Bearer sk-",
                    "accept": "image/*"
                },
                files={
                    "none": ''
                },
                data={
                    "prompt": prompt,
                    "aspect_ratio": "3:2",
                },
            )
            '''
            
            if response.status_code != 200:
                raise Exception("Non-200 response: " + str(response.text))

            data = response.json()

            image_data_list = []
            for i, image in enumerate(data["artifacts"]):
                image_data = image["base64"]
                image_data_list.append(image_data)

            return jsonify({"image_data_list": image_data_list})
        
            '''
            Mit der OpenAI-API
            from openai import OpenAI

            # Ersetze YOUR_API_KEY mit deinem OpenAI-API-Schlüssel
            openai_client = OpenAI(api_key="sk-yourapikey")

            prompt_text = request.args.get('prompt', 'default_prompt')

            response = openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt_text,
                size="1024x1024",
                quality="standard",
                n=1,
            )

            image_url = response.data[0].url

            # Lade das Bild herunter und speichere es lokal
            image_response = requests.get(image_url)
            image_data = base64.b64encode(image_response.content).decode('utf-8')

            # Return the image URL and the base64-encoded image data
            return jsonify({"image_data": image_data})
            '''

    except Exception as e:
        return jsonify({"error": str(e)}), 500

'''
@app.route('/generate_ai', methods=['GET'])
def generate_image():
    try:
        prompt = request.args.get('prompt')
        if prompt is None:
            return jsonify({"error": "Kein Prompt"}), 400

        # Übersetzen des Prompts ins Englisch
        urlT = "https://translate.terraprint.co/translate"
        data = {
            "q": prompt,
            "source": "auto",
            "target": "en"
        }
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(urlT, data=json.dumps(data), headers=headers)
        prompt = response.json()["translatedText"]

        # Bildgenerierung
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

        body = {
        "steps": 40,
        "width": 1024,
        "height": 614,
        "seed": 0,
        "cfg_scale": 5,
        "samples": 1,
        "text_prompts": [
            {
            "text": prompt,
            "weight": 1
            },
            {
            "text": " ",
            "weight": -1
            }
        ],
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer sk-",
        }

        response = requests.post(
            url,
            headers=headers,
            json=body,
        )

        
        response = requests.post(
            f"https://api.stability.ai/v2beta/stable-image/generate/core",
            headers={
                "authorization": f"Bearer sk-",
                "accept": "image/*"
            },
            files={
                "none": ''
            },
            data={
                "prompt": prompt,
                "aspect_ratio": "3:2",
            },
        )
        
        
        if response.status_code != 200:
            raise Exception("Non-200 response: " + str(response.text))

        data = response.json()

        image_data_list = []
        for i, image in enumerate(data["artifacts"]):
            image_data = image["base64"]
            image_data_list.append(image_data)

        return jsonify({"image_data_list": image_data_list})
    
        
        Mit der OpenAI-API
        from openai import OpenAI

        # Ersetze YOUR_API_KEY mit deinem OpenAI-API-Schlüssel
        openai_client = OpenAI(api_key="sk-yourapikey")

        prompt_text = request.args.get('prompt', 'default_prompt')

        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt_text,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url

        # Lade das Bild herunter und speichere es lokal
        image_response = requests.get(image_url)
        image_data = base64.b64encode(image_response.content).decode('utf-8')

        # Return the image URL and the base64-encoded image data
        return jsonify({"image_data": image_data})
        

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
'''

# IP-Adresse des Clients, der die Anfrage senden kann
ALLOWED_IP = "127.0.0.1"    

@app.route('/shutdownServer', methods=['POST'])
def shutdownServer():
    if request.remote_addr == ALLOWED_IP:
        print('Shutting down server...')
        os.kill(os.getpid(), signal.SIGINT)
        return 'Server shutting down...'
    else:
        return 'Access denied'

@app.route('/rebootServer', methods=['POST'])
def restartServer():
    if request.remote_addr == ALLOWED_IP:
        print('Restarting server...')
        os.execl(sys.executable, sys.executable, *sys.argv)
        return 'Server restarting...'
    else:
        return 'Access denied'

@app.route('/reboot', methods=['POST'])
def reboot():
    if request.remote_addr == ALLOWED_IP:
        print('Restarting PlOtter...')
        subprocess.run(['sudo', 'reboot'])
        return 'Rebooting PlOtter...'
    else:
        return 'Access denied'

@app.route('/shutdown', methods=['POST'])
def shutdown():
    if request.remote_addr == ALLOWED_IP:
        print('Shutting down PlOtter...')
        subprocess.run(['sudo', 'shutdown', '-h', 'now'])
        return 'PlOtter shutting down...'
    else:
        return 'Access denied'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
