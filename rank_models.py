# -*- coding: utf-8 -*-
"""rank_models.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1L3I3md7fzBvfjB1G5F6hhnfUGU7HoNM6
"""

import torch
from transformers import AutoModel, AutoTokenizer
from scipy.spatial.distance import cosine
import numpy as np
import csv

# Function to compute cosine similarity
def compute_cosine_similarity(model, tokenizer, sentence1, sentence2):
    # Check and ensure padding token is set
    if tokenizer.pad_token is None:
        if tokenizer.eos_token:
            tokenizer.pad_token = tokenizer.eos_token
        else:
            tokenizer.add_special_tokens({'pad_token': '[PAD]'})

    # Tokenize input sentences
    encoded_input1 = tokenizer(sentence1, return_tensors='pt', padding=True, truncation=True, max_length=128)
    encoded_input2 = tokenizer(sentence2, return_tensors='pt', padding=True, truncation=True, max_length=128)

    # Process through the model
    with torch.no_grad():
        output1 = model(**encoded_input1)
        output2 = model(**encoded_input2)

    # Compute mean of hidden states to derive sentence embeddings
    embedding1 = torch.mean(output1.last_hidden_state, dim=1).squeeze()
    embedding2 = torch.mean(output2.last_hidden_state, dim=1).squeeze()

    # Return cosine similarity score
    return 1 - cosine(embedding1.numpy(), embedding2.numpy())

# Manual implementation of the TOPSIS method
def topsis_method(data, weights, impacts):
    normalized_data = data / np.sqrt((data**2).sum(axis=0))
    weighted_data = normalized_data * weights
    ideal_solution = np.max(weighted_data, axis=0)
    anti_ideal_solution = np.min(weighted_data, axis=0)
    dist_to_ideal = np.sqrt(((weighted_data - ideal_solution)**2).sum(axis=1))
    dist_to_anti_ideal = np.sqrt(((weighted_data - anti_ideal_solution)**2).sum(axis=1))
    score = dist_to_anti_ideal / (dist_to_anti_ideal + dist_to_ideal)
    # Rank models based on score in descending order (higher score is better)
    return np.argsort(-score) + 1  # Adjust rank to be 1-based

# Sample sentence pairs
sentence1 = "The company's revenue has grown by 15% in the last quarter."
sentence2 = "There has been a 15% increase in the company's quarterly revenue."

# List of models to evaluate (modified)
model_identifiers = {
    "albert-base-v2": "ALBERT",
    "roberta-base": "RoBERTa",
    "sentence-transformers/bert-base-nli-mean-tokens": "Sentence-BERT",
    "xlm-roberta-base": "XLM-RoBERTa",  # Replaced GPT-2 with XLM-RoBERTa
    "distilbert-base-uncased": "DistilBERT"
}

# Initialize models and tokenizers
loaded_models = {name: (AutoModel.from_pretrained(id), AutoTokenizer.from_pretrained(id)) for id, name in model_identifiers.items()}

# Calculate similarities
similarities_list = []
model_names = []
for model_id, (model, tokenizer) in loaded_models.items():
    similarity = compute_cosine_similarity(model, tokenizer, sentence1, sentence2)
    similarities_list.append(similarity)
    model_names.append(model_id)
    print(f"Similarity for {model_id}: {similarity}")

# Prepare data for TOPSIS calculation
similarity_data = np.array(similarities_list).reshape(-1, 1)
weights = np.array([1])  # Equal weight for all models
impacts = "max"  # Maximizing similarity

# Apply the TOPSIS ranking method
model_ranks = topsis_method(similarity_data, weights, impacts)

# Sort models based on their rank
sorted_model_ranking = sorted(zip(model_names, model_ranks), key=lambda x: x[1])

# Save the results to a CSV file
with open('model_ranking.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Model Name', 'Rank'])
    for model, rank in sorted_model_ranking:
        writer.writerow([model, int(rank)])