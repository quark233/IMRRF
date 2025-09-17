import argparse
import random
from tqdm import tqdm
import re
import os
import json
from evaluate import print_evaluation_results
from utils.T5 import T5_Question_Answering


def parse_args():
    parser = argparse.ArgumentParser()
    # dataset args
    parser.add_argument('--dataset_name', default='FEVEROUS', type=str)
    parser.add_argument("--model_name", default='flan-t5-xl', type=str)
    args = parser.parse_args()
    return args


def map_direct_answer_to_label(predict):
    predict = predict.lower().strip()
    label_map = {'true': True, 'false': False, 'yes': True, 'no': False, "it's impossible to say": False}
    if predict in label_map:
        return label_map[predict]
    else:
        print(f"Alert!!! wrong answer mapping: {predict}")
        return False


def evaluation(predictions, gt_labels):
        print_evaluation_results(predictions, gt_labels, num_of_classes=2)

def main():
    args = parse_args()
    dataset_name = args.dataset_name
    model_name = args.model_name

    if model_name == 'flan-t5-xl':
        print(f"Loading model {model_name}...")
        model = T5_Question_Answering()

    with open(os.path.join('./datasets', dataset_name, 'claims', 'dev.json'), 'r') as f:
        dataset = json.load(f)

    llm_evidence = 'None'
    summary = 'None'

    llm_evidence_path = f'./data/{dataset_name}_llm_evidence.json'
    summary_path = f'./data/{dataset_name}_KG+wikipedia_summary.json'

    with open(llm_evidence_path, 'r', encoding='utf-8') as f:
        llm_evidence_data = json.load(f)

    with open(summary_path, 'r', encoding='utf-8') as f:
        summary_data = json.load(f)

    gt_labels, predictions = [], []
    results = []

    for sample in tqdm(dataset):
        claim = sample['claim']
        id = sample['id']
        gt_labels.append(sample['label'])

        for llm_evidences in llm_evidence_data:
            if llm_evidences['id'] == id:
                llm_evidence = llm_evidences['llm_evidence']
                break
            
        for summaries in summary_data:
            if summaries['id'] == id:
                summary = summaries['external_evidence_summary']
                break

        answer = model.verify_claim(claim, summary, llm_evidence)['answer_text']
        final_prediction = map_direct_answer_to_label(answer)
        predictions.append('supports' if final_prediction == True else 'refutes')
        results.append({'id': sample['id'],
                        'claim': sample['claim'],
                        'label': sample['label'],
                        'prediction': 'supports' if final_prediction == True else 'refutes'})
        
    evaluation(predictions, gt_labels)

    output_path = f'./data/{dataset_name}_results.json'
    with open(output_path, 'w') as f:
        f.write(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()
    
