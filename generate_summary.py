import os
import json
import argparse
from utils.llm import LLMRequester
from utils.prompt import GENERATE_SUMMARY



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
    
    wikipedia_evidence_path = f"./data/{dataset_name}_wikipedia_evidence.json"
    with open(wikipedia_evidence_path, 'r',encoding='utf-8') as f:
        wikipedia_evidence_dataset = json.load(f)

    KG_evidence_path = f"./data/{dataset_name}_KG_evidence.json"
    with open(KG_evidence_path, 'r',encoding='utf-8') as f:
        KG_evidence_dataset = json.load(f)

    result_dict = {}
    outputs = []

    for idx, sample in enumerate(wikipedia_evidence_dataset[:3]):
        result = {
            'idx': idx,
            'id': sample['id'],
            'claim': sample['claim'],
            'external_evidence_summary': ''
        }

        result_dict[sample['id']] = result
        wikipedia_evidence = '\n'.join(sample['wikipedia_evidence'])

        for KG_sample in KG_evidence_dataset:
            if KG_sample['id']==sample['id']:
                KG_evidence = '\n'.join(KG_sample['wikidata_evidence'])

        prompt = GENERATE_SUMMARY.format(claim=sample['claim'], paragraph1=wikipedia_evidence, paragraph2=KG_evidence)
        summary = llm.generate(model, prompt)
        result_dict[sample['id']]['external_evidence_summary'] = summary
        output_file_path = f'./data/{dataset_name}_{model}_KG+wikipedia_summary.json'

        if os.path.exists(output_file_path):
            with open(output_file_path, 'r', encoding='utf-8') as f:
                outputs = json.load(f)
        
        outputs.append(result_dict[sample['id']])
        sorted_outputs = sorted(outputs, key=lambda x: x['idx'])
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_outputs, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()


