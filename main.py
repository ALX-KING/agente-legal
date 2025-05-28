from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

app = FastAPI()

conn = sqlite3.connect('memoria_clientes.db'check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS historial (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_cliente TEXT,
    mensaje_usuario TEXT,
    respuesta_agente TEXT
)
''')
conn.commit()

class Consulta(BaseModel):
    nombre_cliente: str
    consulta: str

@app.post('/consulta')
def responder_consulta(consulta: Consulta):
    cursor.execute('SELECT mensaje_usuario, respuesta_agente FROM historial WHERE nombre_cliente = ?', (consulta.nombre_cliente,))
    historial = cursor.fetchall()

    mensajes = [{"role": "system", "content": "Eres un asistente legal experto en el Código Civil, Comercial y Penal de la República Argentina."}]
    for mensaje_usuario, respuesta_agente in historial:
        mensajes.append({"role": "user", "content": mensaje_usuario})
        mensajes.append({"role": "assistant", "content": respuesta_agente})
    mensajes.append({"role": "user", "content": consulta.consulta})

    respuesta = openai.ChatCompletion.create(
        model="gpt-4",
        messages=mensajes
    ).choices[0].message["content"]

    cursor.execute('INSERT INTO historial (nombre_cliente, mensaje_usuario, respuesta_agente) VALUES (?, ?, ?)',
                   (consulta.nombre_cliente, consulta.consulta, respuesta))
    conn.commit()

    return {"respuesta": respuesta}

@app.get('/historial/{nombre_cliente}')
def obtener_historial(nombre_cliente: str):
    cursor.execute('SELECT mensaje_usuario, respuesta_agente FROM historial WHERE nombre_cliente = ?', (nombre_cliente,))
    historial = cursor.fetchall()
    return {"historial": historial}
