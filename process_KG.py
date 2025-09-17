import os
import time
import re
import json
import argparse
from utils.llm import LLMRequester
from utils.prompt import PROCESS_KG


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_name', default='FEVEROUS', type=str)
    parser.add_argument('--model_name', default='gpt-3.5-turbo',type=str)
    return parser.parse_args()
    

def main():
    args = parse_args()
    dataset_name = args.dataset_name
    model = args.model_name
    llm = LLMRequester()

    original_KG_evidence_path = f"./data/{dataset_name}_KG_original_evidence.json"
    with open(original_KG_evidence_path, 'r',encoding='utf-8') as f:
        original_KG_evidence = json.load(f)

    pattern = r'\d+\.\s.*'

    processed_results = {}
    outputs = []

    for sample in original_KG_evidence:
        processed_result={
            'idx': sample['idx'],
            "id": sample['id'],
            "claim": sample['claim'],
            "wikidata_evidence": []
        }
        processed_results[sample['id']] = processed_result

        KG_results = sample['wikidata_evidence']
        if KG_results:
            prompt = PROCESS_KG.format(KG_results=KG_results)
            response = llm.generate(model, prompt)
            matches = re.findall(pattern, response)
            processed_results[sample['id']]["wikidata_evidence"] = matches
            if not matches:
                processed_results[sample['id']]["wikidata_evidence"] = [response]
        else:
            processed_results[sample['id']]["wikidata_evidence"] = ["None"]

        output_file_path = f'./data/{dataset_name}_KG_evidence.json'

        if os.path.exists(output_file_path):
            with open(output_file_path, 'r', encoding='utf-8') as f:
                outputs = json.load(f)
        outputs.append(processed_results[sample['id']])

        sorted_outputs = sorted(outputs, key=lambda x: x['idx'])
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_outputs, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
