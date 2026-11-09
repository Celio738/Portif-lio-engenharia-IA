# CAEd NLP Challenge - Avaliação de Complexidade Textual

Este projeto foi desenvolvido como parte do processo seletivo da Fundação CAEd (Área de Inovação e Inteligência Artificial). O sistema implementa um pipeline de Processamento de Linguagem Natural (PLN) projetado para classificar fragmentos de textos didáticos em quatro níveis escolares e aplicar operadores de mutação sintática.

## 🎯 Objetivos do Projeto

1. **Pré-processamento:** Fragmentação de textos didáticos longos em sentenças.
2. **Feature Engineering:** Cálculo da "taxa de canonicidade" (padrão CV - Consoante/Vogal) das palavras, conforme exigido no edital.
3. **Classificação:** Treinamento de um modelo `RandomForestClassifier` com vetorização TF-IDF para prever a complexidade do texto.
4. **Mutação Sintática:** Aplicação de um operador de "Troca de Palavras" por sinônimos utilizando o WordNet, avaliando o impacto da mutação na classificação final do modelo.

## ⚙️ Pré-requisitos e Configuração

Certifique-se de ter o **Python 3.10+** instalado em sua máquina.

1. **Clone ou extraia o repositório:**
   Abra o terminal na pasta raiz do projeto.

2. **Crie e ative um ambiente virtual:**
   ```bash
   python -m venv venv
   # No Windows (PowerShell/CMD):
   .\venv\Scripts\activate
   # No Git Bash:
   source venv/Scripts/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Baixe os modelos linguísticos necessários (spaCy e NLTK):**
   ```bash
   python -m spacy download pt_core_news_sm
   
   python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('wordnet'); nltk.download('omw-1.4'); nltk.download('omw-2.0')"
   ```

## 📁 Estrutura de Diretórios

```text
DESAFIO_CAED_NLP/
│
├── data/
│   ├── processed/         # Dataset gerado, modelo treinado e vetorizador salvos
│   └── raw/               # Textos brutos originais separados por nível escolar
│
├── src/                   # Scripts principais do pipeline
│   ├── data_loader.py     # ETL, leitura e fragmentação (spaCy)
│   ├── features.py        # Algoritmo de classificação de canonicidade (pyphen)
│   ├── model.py           # Treinamento do modelo RandomForest e avaliação
│   └── mutation.py        # Operador de mutação e teste de inferência
│
├── README.md              # Documentação de execução
└── requirements.txt       # Bibliotecas e versões
```

## 🚀 Como Executar (Passo a Passo)

Para rodar o projeto do início ao fim, navegue até a pasta `src/` e execute os scripts na seguinte ordem:

```bash
cd src
```

**1. Extração e Limpeza**
```bash
python data_loader.py
```
*Lê os arquivos `.txt` da pasta `data/raw`, fragmenta em frases e salva o dataset em `data/processed/dataset_fragmentado.csv`.*

**2. Treinamento do Modelo**
```bash
python model.py
```
*Calcula a taxa de canonicidade para todas as frases, vetoriza os textos, treina o modelo de classificação e imprime o relatório de métricas na tela. Salva o modelo treinado localmente.*

**3. Teste de Mutação**
```bash
python mutation.py
```
*Recebe exemplos de textos (complexos e simples), aplica a mutação de sinônimos via WordNet e verifica se a troca das palavras alterou o nível de complexidade predito pelo modelo.*

## 🛠️ Tecnologias Utilizadas
* **Python:** Linguagem principal.
* **Pandas / NumPy:** Manipulação e estruturação de dados.
* **Scikit-learn:** Treinamento do modelo de Machine Learning (Random Forest) e vetorização TF-IDF.
* **spaCy:** NLP para tokenização e segmentação de sentenças.
* **NLTK (WordNet):** Busca e substituição léxica (sinônimos).
* **Pyphen:** Lógica de hifenização e contagem silábica.