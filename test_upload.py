#!/usr/bin/env python3
"""
Teste de upload de imagens
Este script demonstra como usar a API de upload de imagens
"""

import requests
import os
import sys

def test_image_upload(server_url="http://localhost:8000", image_path=None, user_id=None):
    """
    Testa o upload de imagem
    
    Args:
        server_url: URL do servidor Django
        image_path: Caminho para o arquivo de imagem
        user_id: ID do usuário (opcional)
    """
    
    if not image_path:
        print("Erro: Caminho da imagem não fornecido")
        return False
    
    if not os.path.exists(image_path):
        print(f"Erro: Arquivo não encontrado: {image_path}")
        return False
    
    upload_url = f"{server_url}/api/images/upload/"
    
    try:
        # Preparar o arquivo para upload
        with open(image_path, 'rb') as img_file:
            files = {'image': img_file}
            data = {}
            
            if user_id:
                data['user_id'] = user_id
            
            # Fazer o upload
            response = requests.post(upload_url, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print("✅ Upload realizado com sucesso!")
                    print(f"ID da imagem: {result['image_id']}")
                    print(f"Caminho do arquivo: {result['file_path']}")
                    print(f"Hash do arquivo: {result['file_hash']}")
                    print(f"Nome original: {result['original_filename']}")
                    print(f"Tamanho: {result['file_size']} bytes")
                    if result.get('duplicate'):
                        print("⚠️  Imagem já existe no sistema")
                    return True
                else:
                    print(f"❌ Erro no upload: {result['error']}")
                    return False
            else:
                print(f"❌ Erro HTTP {response.status_code}: {response.text}")
                return False
                
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao servidor")
        print("Certifique-se de que o servidor Django está rodando")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return False

def list_images(server_url="http://localhost:8000", user_id=None, limit=10):
    """Lista as imagens no sistema"""
    
    list_url = f"{server_url}/api/images/list/"
    params = {'limit': limit}
    
    if user_id:
        params['user_id'] = user_id
    
    try:
        response = requests.get(list_url, params=params)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                images = result['images']
                print(f"\n📋 Lista de imagens (Total: {result['total_count']}):")
                print("-" * 80)
                
                for img in images:
                    print(f"ID: {img['id']}")
                    print(f"Nome: {img['original_filename']}")
                    print(f"Tamanho: {img['file_size']} bytes")
                    print(f"Upload por: {img['uploaded_by'] or 'Anônimo'}")
                    print(f"Data: {img['uploaded_at']}")
                    print("-" * 40)
                
                return True
            else:
                print(f"❌ Erro ao listar: {result['error']}")
                return False
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Teste de Upload de Imagens")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Uso: python test_upload.py <caminho_da_imagem> [user_id]")
        print("ou: python test_upload.py list [user_id]")
        print("\nExemplo:")
        print("  python test_upload.py /path/to/image.jpg")
        print("  python test_upload.py /path/to/image.jpg 1")
        print("  python test_upload.py list")
        print("  python test_upload.py list 1")
        sys.exit(1)
    
    if sys.argv[1] == "list":
        user_id = sys.argv[2] if len(sys.argv) > 2 else None
        success = list_images(user_id=user_id)
    else:
        image_path = sys.argv[1]
        user_id = sys.argv[2] if len(sys.argv) > 2 else None
        success = test_image_upload(image_path=image_path, user_id=user_id)
    
    if not success:
        sys.exit(1)