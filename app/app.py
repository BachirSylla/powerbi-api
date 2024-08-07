import requests
import json
import logging
from flask import Flask, jsonify, request
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
import os

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Chemin vers le certificat .p12
p12_cert_path = 'D:/get-project-entree/powerBI/app/application_de_test.p12'
p12_password = 'password'  # Remplacez par le mot de passe réel du certificat

def get_api_data(start_date, end_date, app_name, operation):
    logging.debug("Début de get_api_data")
    
    # Nettoyer les paramètres pour enlever les espaces blancs et les retours à la ligne
    start_date = start_date.strip()
    end_date = end_date.strip()
    app_name = app_name.strip()
    operation = operation.strip()
    
    # Construire l'URL de l'API
    url = f"https://rasign.gainde2000.sn:8443/app_signatureV1.1/signer/v1.1/liste_cert_sign/{start_date}/{end_date}/{app_name}/{operation}"
    logging.debug(f"URL construite: {url}")

    # Charger le fichier P12
    try:
        with open(p12_cert_path, 'rb') as p12_f:
            p12_data = p12_f.read()
        p12 = pkcs12.load_key_and_certificates(p12_data, p12_password.encode('utf-8'))
    except Exception as e:
        logging.error(f"Erreur lors du chargement du fichier P12: {e}")
        return {'error': 'Failed to load certificate', 'status_code': 500, 'message': str(e)}

    # Extraire le certificat et la clé privée
    cert = p12[1]  # Ceci est l'objet certificat
    key = p12[0]   # Ceci est l'objet clé privée

    try:
        # Sauvegarder le certificat et la clé dans des fichiers temporaires
        with open('temp_cert.pem', 'wb') as cert_file:
            cert_file.write(cert.public_bytes(Encoding.PEM))

        with open('temp_key.pem', 'wb') as key_file:
            key_file.write(key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()))

        # Faire la requête à l'API
        response = requests.get(url, cert=('temp_cert.pem', 'temp_key.pem'))
        logging.debug(f"Réponse de l'API: {response.status_code}")
        logging.debug(f"Contenu de la réponse: {response.text}")
    except Exception as e:
        logging.error(f"Erreur lors de la requête API: {e}")
        return {'error': 'Failed to retrieve data', 'status_code': 500, 'message': str(e)}
    finally:
        # Nettoyer les fichiers temporaires
        if os.path.exists('temp_cert.pem'):
            os.remove('temp_cert.pem')
        if os.path.exists('temp_key.pem'):
            os.remove('temp_key.pem')

    if response.status_code == 200:
        return response.json()
    else:
        return {'error': 'Failed to retrieve data', 'status_code': response.status_code, 'message': response.text}

@app.route('/get_data', methods=['GET'])
def get_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    app_name = request.args.get('app_name')
    operation = request.args.get('operation')

    logging.debug(f"Requête reçue avec les paramètres: start_date={start_date}, end_date={end_date}, app_name={app_name}, operation={operation}")

    if not start_date or not end_date or not app_name or not operation:
        return jsonify({'error': 'Missing parameters'}), 400

    data = get_api_data(start_date, end_date, app_name, operation)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
