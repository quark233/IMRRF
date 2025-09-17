import os
from openai import OpenAI
import re
import json
import argparse
from utils.llm import LLMRequester
from utils.prompt import GENERATE_EVIDENCE

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_name', default='FEVEROUS', type=str)
    parser.add_argument('--model_name', default='gpt-4o',type=str)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    dataset_name = args.dataset_name
    model = args.model_name
    llm = LLMRequester()
    pattern = r'\d+\.\s.*'

    summary_path = f"./data/{dataset_name}_KG+wikipedia_summary.json"
    with open(summary_path, 'r',encoding='utf-8') as f:
        summary_dataset = json.load(f)

    result_dict = {}
    outputs = []

    for idx, sample in enumerate(summary_dataset):
        result = {
        'idx': idx,
        'id': sample['id'],
        'claim': sample['claim'],
        'llm_evidence': []
    }
        result_dict[sample['id']] = result

        claim=sample['claim']
        summary=sample['external_evidence_summary']

        prompt = GENERATE_EVIDENCE.format(claim=claim, summary=summary)
        evidence = llm.generate(model, prompt)
        matches = re.findall(pattern, evidence)
        result_dict[sample['id']]['llm_evidence']=matches
        if not matches:
            result_dict[sample['id']]['llm_evidence']=[evidence]

        output_file_path = f'./data/{dataset_name}_llm_evidence.json'
        if os.path.exists(output_file_path):
            with open(output_file_path, 'r', encoding='utf-8') as f:
                outputs = json.load(f)
        
        outputs.append(result_dict[sample['id']])
        sorted_outputs = sorted(outputs, key=lambda x: x['idx'])
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_outputs, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()

