#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: gleb diakonov
"""

import streamlit as st
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import BertTokenizer, BertModel
import re

MAX_LEN = 256

def is_ok(text):
    if not text:
        match = True
    else:
        match = re.match("[a-z]+", text)
                         
    return bool(match)

@st.cache_data
def define_tokenizer():
    tokenizer = BertTokenizer.from_pretrained('./token')
    return tokenizer

def preprocess(text):
    
    tokenizer = define_tokenizer()
    
    encoded_text = tokenizer.encode_plus(
        text,
        max_length=MAX_LEN,
        add_special_tokens=True,
        return_token_type_ids=True,
        pad_to_max_length=True,
        return_attention_mask=True,
        return_tensors='pt',
        )

    input_ids = encoded_text['input_ids']
    attention_mask = encoded_text['attention_mask']
    token_type_ids = encoded_text['token_type_ids']     
    
    return input_ids, attention_mask, token_type_ids

class BERTClass(torch.nn.Module):
    def __init__(self):
        super(BERTClass, self).__init__()
        self.bert_model = BertModel.from_pretrained('./bert')
        self.dropout = torch.nn.Dropout(0.3)
        self.linear = torch.nn.Linear(768, 12)

    def forward(self, input_ids, attn_mask, token_type_ids):
        output = self.bert_model(
            input_ids, 
            attention_mask=attn_mask, 
            token_type_ids=token_type_ids
        )
        output_dropout = self.dropout(output.pooler_output)
        output = self.linear(output_dropout)
        return output

@st.cache_data
def configure_model():
    model = BERTClass()
    model.load_state_dict(torch.load('model_state_dict.pt', map_location = 'cpu'))
    return model

def predict(text):
    
    model = configure_model()
    model.eval()

    target_idxs = ['Astrophysics', 'Condensed matter', 
                   'Computer Science', 'Electrical Engineering and Systems Science', 
                   'General Relativity and Quantum Cosmology', 'High Energy Physics - Phenomenology', 
                   'High Energy Physics - Theory', 'Mathematics', 
                   'Mathematical Physics', 'Physics',
                   'Quantum Physics', 'Statistics']
    
    with torch.no_grad():
    
        input_ids, attention_mask, token_type_ids = preprocess(text)
        preds = model(input_ids, attention_mask, token_type_ids)
        output = F.softmax(preds, dim = 1).detach()
        output = output.flatten().numpy()
        output = {tag: round(float(prob)*100, 2) for tag, prob in zip(target_idxs, output)}
        outputs = {k: v for k, v in sorted(output.items(), reverse = True, key = lambda x: x[1])}
        
    return outputs


if __name__ == '__main__':
    
    st.markdown("<h1 style='text-align: center;'>Find out the topic of the article</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>Please enter title or summary</h2>", unsafe_allow_html=True)
    form = st.form("my_form")
    title = form.text_input("TITLE")
    summary = form.text_area("SUMMARY")
    button = form.form_submit_button("Submit")
    summary = summary.lower()
    title = title.lower()
    if button:
        if not title and not summary:
            st.write("**PLEASE ENTER SOMETHING!**")
        else:
            text = title + ". " + summary
        
            if not is_ok(summary) and is_ok(title):
                st.write("**INCORRECT INPUT FORMAT: SUMMARY**")
            if is_ok(summary) and not is_ok(title):
                st.write("**INCORRECT INPUT FORMAT: TITLE**")
            elif not is_ok(title) and not is_ok(summary):
                st.write("**INCORRECT INPUT FORMAT: TITLE, SUMMARY**")
            elif len(summary.split()) in (1,2,3) and not title:
                st.write("**There are too few words in summary, result can be bad. Make shure you enter full text**")
            elif len(title.split()) in (1,2,3) and not summary:
                st.write("**There are too few words in title, result can be bad. Make shure you enter full text**")
            elif len(title.split()) in (1,2,3) and len(summary.split()) == 1:
                st.write("**There are too few words in title and summary, result can be bad. Make shure you enter full text**")
            else:
                outputs = predict(text)
                sums_probs = []
                for k, v in outputs.items(): 
                    st.write(f'Topic:  **:blue[{k}]**, probability: **:green[{v}%]**')
                    sums_probs.append(v)
                    if sum(sums_probs) >= 95:
                        break
                
                