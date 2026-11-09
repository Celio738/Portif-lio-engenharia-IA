import os
import pandas as pd
import spacy


print("Carregando modelo do spaCy...")
nlp = spacy.load("pt_core_news_sm")

def carregar_e_fragmentar(diretorio_base):
    dados = []
    print(f"Lendo arquivos da pasta: {diretorio_base}")
    
   
    for nivel in os.listdir(diretorio_base):
        caminho_nivel = os.path.join(diretorio_base, nivel)
        
        
        if os.path.isdir(caminho_nivel):
            print(f"Processando nível: {nivel}")
            
           
            for arquivo in os.listdir(caminho_nivel):
                if arquivo.endswith('.txt'):
                    caminho_arquivo = os.path.join(caminho_nivel, arquivo)
                    
                    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                        texto = f.read()
                        doc = nlp(texto)
                        
                        
                        for sentenca in doc.sents:
                            texto_limpo = sentenca.text.strip()
                            
                            
                            if len(texto_limpo) > 15: 
                                dados.append({
                                    'texto': texto_limpo, 
                                    'nivel': nivel,
                                    'arquivo_origem': arquivo
                                })
                                
    print(f"\nTotal de fragmentos extraídos: {len(dados)}")
    
    
    df = pd.DataFrame(dados)
    
    
    caminho_saida = '../data/processed/dataset_fragmentado.csv'
    df.to_csv(caminho_saida, index=False, encoding='utf-8')
    print(f"Dataset salvo com sucesso em: {caminho_saida}")
    
    return df


if __name__ == "__main__":
    df_final = carregar_e_fragmentar('../data/raw')
    print("\nVisualização das primeiras linhas:")
    print(df_final.head())