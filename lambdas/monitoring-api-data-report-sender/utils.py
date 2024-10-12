import os
import json
import requests
from tenacity import retry, stop_after_attempt
from datetime import datetime

MAILGUN_APIKEY = os.environ.get("MAILGUN_APIKEY")
MAILGUN_URL = os.environ.get("MAILGUN_URL")
COHERE_APIKEY = os.environ.get("COHERE_APIKEY")
COHERE_URL = os.environ.get("COHERE_URL")
COHERE_QUERY = os.environ.get("COHERE_QUERY")


@retry(
    reraise=True,
    stop=stop_after_attempt(3)
)
def send_request_to_cohere(html, results):
    headers = {
      'Content-Type': 'application/json',
      'Authorization': f'Bearer {COHERE_APIKEY}'
    }
    
    text = f"{COHERE_QUERY} \n\n {html} \n\n {str(results)}"
    payload = json.dumps({
      "message": text
    })
    response = requests.request("POST", COHERE_URL, headers=headers, data=payload)
    response.raise_for_status()
    return response.json()


def get_sensors_data(database, user_id):
    sensors_data_collection = database['sensors_data']
    
    today_date = datetime.now()

    date_from = datetime(
        today_date.year,
        today_date.month,
        today_date.day - 18,
        00,
        00,
        00
    )

    date_to = datetime(
        today_date.year,
        today_date.month,
        today_date.day + 1,
        23,
        59,
        59
    )

    cursor = sensors_data_collection.find({
        "timestamp": {
            '$gte': date_from,
            '$lt': date_to
        },
        "user_id": str(user_id)
    }, {'_id':0, 'user_id': 0})

    return list(cursor)


@retry(
    reraise=True,
    stop=stop_after_attempt(3)
)
def send_email(cohere_response, user_email):

    payload = {
        'from': 'Mailgun Sandbox <postmaster@sandbox2d9f1b7e5dd14022b393858c35050203.mailgun.org>',
        'to': f'IoT Management API <{user_email}>',
        'subject': 'IoT Management API - Reporte Semanal',
        'html': cohere_response
    }

    response = requests.post(MAILGUN_URL,auth=("api", MAILGUN_APIKEY),data=payload)
    response.raise_for_status()
    
    return response


html_report = html = """<!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reporte Semanal</title>
        <style>
            /* General email styles */
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }
            .email-container {
                width: 100%;
                max-width: 800px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .header {
                background-color: #4CAF50;
                padding: 20px;
                text-align: center;
                color: white;
            }
            .header h1 {
                margin: 0;
                font-size: 24px;
            }
            .header p {
                font-size: 16px;
            }
            .content {
                padding: 20px;
            }
            .content h2 {
                color: #333;
            }
            .content p {
                font-size: 14px;
                line-height: 1.6;
                color: #555;
            }
            .content strong {
                color: #4CAF50;
            }
            .report-section {
                background-color: #f9f9f9;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
            }
            .footer {
                background-color: #333;
                color: #fff;
                text-align: center;
                padding: 10px;
            }
            .footer p {
                font-size: 12px;
                margin: 0;
            }
            .btn-primary {
                background-color: #4CAF50;
                color: white;
                text-decoration: none;
                padding: 10px 20px;
                border-radius: 5px;
                display: inline-block;
            }
            .btn-primary:hover {
                background-color: #45a049;
            }
            /* Responsive */
            @media only screen and (max-width: 800px) {
                .email-container {
                    width: 100%;
                }
            }
        </style>
    </head>
    <body>
        <div class="email-container">
            <!-- Header -->
            <div class="header">
                <h1>Reporte Semanal</h1>
                <p>Análisis y recomendaciones basado en tus sensores</p>
            </div>

            <!-- Content -->
            <div class="content">
                <h2>¡Hola, {{usuario}}!</h2>
                <p>Te compartimos nuestro reporte semanal en base al análisis realizado de las mediciones obtenidas por tus sensores.</p>

                <!-- Sección del análisis de sensores -->
                <div class="report-section">
                    <p>{{cohere_analysis}}</p>
                </div>

                <p>Espero que este resumen sea de utilidad y pueda ayudar a mejorar la gestión y monitoreo de tus sistemas.</p>
                <p>¡Nos vemos la próxima!</p>

            </div>
        </div>
    </body>
    </html>
    """
