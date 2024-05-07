from fastapi import FastAPI, HTTPException
from pdfminer.high_level import extract_text
from docx import Document
import aiohttp
import tiktoken
import os
import csv

import csv
from docx import Document
import os

app = FastAPI()

async def download_file(url: str, path: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.read()
                with open(path, 'wb') as f:
                    f.write(data)
                if not os.path.exists(path) or os.path.getsize(path) == 0:
                    raise HTTPException(status_code=400, detail="Erro ao salvar o arquivo.")
            else:
                raise HTTPException(status_code=response.status, detail="Erro ao baixar o arquivo.")

def read_pdf_to_string(filepath: str) -> str:
    text = extract_text(filepath)
    return text

def extract_text_from_docx(filepath: str) -> str:
    try:
        doc = Document(filepath)
        full_text = []
        for paragraph in doc.paragraphs:
            full_text.append(paragraph.text)
        return '\n'.join(full_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler arquivo DOCX: {str(e)}")

def extract_text_from_csv(filepath: str, column_index: int) -> str:
    text = ""
    with open(filepath, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) > column_index:
                text += row[column_index] + "\n"
    return text

def read_txt_to_string(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as file:
        text = file.read()
    return text

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

@app.get("/count-tokens/")
async def count_tokens(url: str, encoding_name: str = "cl100k_base"):
    file_path = "tempfile"
    if url.lower().endswith('.pdf'):
        file_path += ".pdf"
    elif url.lower().endswith('.txt'):
        file_path += ".txt"
    elif url.lower().endswith('.docx'):
        file_path += ".docx"
    elif url.lower().endswith('.csv'):
        file_path += ".csv"
    else:
        raise HTTPException(status_code=400, detail="Formato de arquivo não suportado. Use PDF, TXT, CSV ou DOCX.")
    
    await download_file(url, file_path)
    
    try:
        if file_path.endswith('.pdf'):
            text = read_pdf_to_string(file_path)
        elif file_path.endswith('.txt'):
            text = read_txt_to_string(file_path)
        elif file_path.endswith('.docx'):
            text = extract_text_from_docx(file_path)
        elif file_path.endswith('.csv'):
            text = extract_text_from_csv(file_path, column_index=0)  # Supondo que você quer ler a primeira coluna
        else:
            raise HTTPException(status_code=400, detail="Formato de arquivo não suportado.")
    finally:
        os.remove(file_path)  # Remove o arquivo temporário independentemente de sucesso ou falha na leitura
    
    tokens = num_tokens_from_string(text, encoding_name)
    return {"Número de tokens": tokens}