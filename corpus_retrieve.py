import argparse
from tqdm import tqdm
import os
import json
from retriever import PyseriniRetriever


def parse_args():
    parser = argparse.ArgumentParser()
    # dataset args
    parser.add_argument('--dataset_name', default='FEVEROUS', type=str)
    parser.add_argument('--data_path', default='./datasets', type=str)
    parser.add_argument('--corpus_evidence_dir', type=str)
    
    # fact checker args
    parser.add_argument('--corpus_index_path', default=None, type=str)
    parser.add_argument('--num_retrieved', default=5, type=int)
    parser.add_argument('--max_evidence_length', default=3000, help='to avoid exceeding GPU memory', type=int)
    args = parser.parse_args()
    return args


class CorpusRetrieve:
    def __init__(self, args) -> None:
        # load model
        self.args = args
        self.searcher = PyseriniRetriever(self.args.corpus_index_path, use_bm25=True, k1=0.9, b=0.4)

    def retrieve_evidence(self, query):
        hits = self.searcher.retrieve(query, self.args.num_retrieved)
        evidence_list = []
        for idx, hit in enumerate(hits, start=1):
            evidence_list.append(f"{idx}. {hit['text'].strip()}")

        # cut overlong evidence
        if len(evidence_list) > self.args.max_evidence_length:
            print('evidence is too long, cut it to max_evidence_length')
            evidence_list = evidence_list[:self.args.max_evidence_length]

        retrieved_results = []
        for hit in hits:
            retrieved_results.append({'id': hit['doc_id'], 'score': hit['score'], 'query': query})

        return evidence_list, retrieved_results

    def execute(self):
        
        with open(os.path.join('./datasets', self.args.dataset_name, 'claims', 'dev.json'), 'r') as f:
            raw_dataset = json.load(f)

        evidence_result=[]
        wikipedia_evidences = {}
        outputs = []
        for idx, sample in enumerate(tqdm(raw_dataset)):
            wikipedia_evidence = {'idx': idx,
                                  'id': sample['id'],
                                  'claim': sample['claim'],
                                  'wikipedia_evidence': []}
            wikipedia_evidences[sample['id']] = wikipedia_evidence
            evidence, retrieved_results = self.retrieve_evidence(sample['claim'])
            wikipedia_evidences[sample['id']]['wikipedia_evidence'] = evidence

        for key in wikipedia_evidences:
            outputs.append(wikipedia_evidences[key])

        sorted_outputs = sorted(outputs, key=lambda x: x['idx'])

        if not os.path.exists(self.args.corpus_evidence_dir):
            os.makedirs(self.args.corpus_evidence_dir)

        wikipedia_evidence_file_name = f'./data/{self.args.dataset_name}_wikipedia_evidence.json'
        outputs_file_path = os.path.join(self.args.corpus_evidence_dir, wikipedia_evidence_file_name)

        with open(outputs_file_path, 'w',encoding='utf-8') as f:
            json.dump(sorted_outputs, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    args = parse_args()
    program_executor = CorpusRetrieve(args)
    program_executor.execute()